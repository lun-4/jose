import discord
from discord.ext import commands
import time
from random import SystemRandom
random = SystemRandom()

import sys
import subprocess
import importlib
import copy
import gc

sys.path.append("..")
import jauxiliar as jaux
import josecommon as jcommon
import joseerror as je

DEFAULT_BLOCKS_JSON = '''{
    "guilds": [],
    "users": []
}'''

NEW_BACKEND = ['']

class JoseBot(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)
        self.nick = 'jose-bot'
        self.modules = {}

        self.client.modules = self.modules
        self.client.jose = self

        self.env = {
            'cooldowns': {},
        }

        self.start_time = time.time()
        self.command_lock = False
        self.dev_mode = False
        self.made_gshutdown = False

        self.jsondb('blocks', path='db/blocks.json', default=DEFAULT_BLOCKS_JSON)
        self.ev_empty()

    async def do_dev_mode(self):
        self.logger.info("Developer Mode Enabled")
        g = discord.Game(name='JOSÉ IN MAINTENANCE', url='fuck you')
        await self.client.change_presence(game=g)

    def ev_empty(self):
        self.event_tbl = {
            'on_message': [],
            'any_message': [],
            'server_join': [],
            'client_ready': [],
            'socket_response': [],

            # member stuff
            'member_join': [],
            'member_remove': [],
            'server_remove': [],
        }

    def ev_load(self, dflag=False):
        # register events
        count = 0

        for modname in self.modules:
            module = self.modules[modname]
            modinst = self.modules[modname]['inst']
            for method in module['handlers']:
                evname = method[method.find("_")+1:]

                if dflag:
                    self.logger.info("Event handler %s@%s:%s", \
                        method, modname, evname)

                # check if event exists
                if evname not in self.event_tbl:
                    self.logger.warning("Event %s@%s:%s doesn't exist in Event Table, creating", \
                        method, modname, evname)

                    self.event_tbl[evname] = []

                try:
                    handler = getattr(modinst, method)
                except Exception as err:
                    self.logger.error("fuck", exc_info=True)
                    sys.exit(0)

                self.event_tbl[evname].append(handler)
                count += 1

        self.logger.info("[ev_load] Loaded %d handlers" % count)

    async def unload_mod(self, modname):
        module = self.modules[modname]
        instance = module['inst']

        if not hasattr(instance, 'ext_unload'):
            self.logger.error("%s doesn't have ext_unload", modname)
            return False, "ext_unload isn't available in %s" % (modname)

        try:
            ok = await instance.ext_unload()

            # first, we should, at least, remove the commands the module has
            # it will help a LOT on memory usage.
            instance_methods = (method for method in dir(instance)
                if callable(getattr(instance, method)))

            for method in instance_methods:
                if method.startswith('c_'):
                    # command, remove it
                    delattr(self, method)

            # delete stuff from the module table
            del instance_methods, self.modules[modname]

            # remove its events from the evt. table, if any
            if len(module['handlers']) > 0:
                self.ev_empty()
                self.ev_load()

            self.logger.info("[unload_mod] Unloaded %s", modname)
            return ok
        except Exception as e:
            self.logger.error("[ERR][unload_mod]%s: %s", (modname, repr(e)))
            return False, repr(e)


    async def unload_all(self):
        # unload all modules

        # copy.copy doesn't work on dict_keys objects
        to_remove = []
        for key in self.modules:
            to_remove.append(key)

        count = 0
        for modname in to_remove:
            ok = await self.unload_mod(modname)
            if not ok:
                self.logger.error("[unload_all] %s didn't return a True", modname)
                return ok
            count += 1

        self.logger.info("[unload_all] Unloaded %d out of %d modules", \
            count, len(to_remove))

        return True, ''

    async def get_module(self, name):
        if name in self.modules:
            # Already loaded module, unload it

            mod = self.modules[name]
            try:
                ok = await mod['inst'].ext_unload()
                if not ok[0]:
                    self.logger.error("Error on ext_unload(%s): %s", name, ok[1])
                    return False
            except Exception as e:
                self.logger.warn("Almost unloaded %s: %s", name, repr(e))
                return False

            # import new code
            return importlib.reload(mod['module'])
        else:
            # import
            return importlib.import_module('ext.%s' % name)

    async def mod_instance(self, name, classobj):
        instance = classobj(self.client)

        # set its logger
        instance.logger = jcommon.logger.getChild(name)

        if not hasattr(instance, 'ext_load'):
            self.logger.error("Module not compatible with EAPI")
            return False

        # hey thats p good
        try:
            ok = await instance.ext_load()
            if not ok[0]:
                self.logger.error("Error happened on ext_load(%s): %s", name, ok[1])
                return False
            else:
                return instance
        except Exception as e:
            self.logger.warn("Almost loaded %s", name, exc_info=True)
            return False

    async def register_mod(self, name, class_name, module, instance):
        instance_methods = (method for method in dir(instance)
            if callable(getattr(instance, method)))

        # create module in the... module table... yaaaaay...
        self.modules[name] = ref = {
            'inst': instance,
            'class': class_name,
            'module': module,
        }

        methods = []
        handlers = []

        for method in instance_methods:
            stw = str.startswith
            if stw(method, 'c_'):
                # command
                setattr(self, method, getattr(instance, method))
                methods.append(method)

            elif stw(method, 'e_'):
                # Event handler
                handlers.append(method)

        # copy them and kill them
        ref['methods'] = copy.copy(methods)
        ref['handlers'] = copy.copy(handlers)
        del methods, handlers

        # done
        return True

    def load_new_backend(self, name):
        # ok so, gotta be ready
        # we need to make SURE the new module can handle discord.py's cogs
        # the last thing we need to do is run bot.add_cog

        module_name = "ext.{}".format(name)
        module = importlib.import_module(module_name)
        importlib.reload(module)

        instance = module.setup(self.client)
        instance_methods = (method for method in dir(instance) \
            if callable(getattr(instance, method)))

        # this is a giant hack
        stw = str.startswith
        for method in instance_methods:
            if stw(method, 'c_'):

                async def cmd(self, ctx):
                    t = time.time()
                    jcxt = jcommon.Context(self.client, ctx.message, t, self)
                    await method(instance, ctx.message, \
                        ctx.message.content.split(' '), jcxt)

                cmd = commands.group(pass_context=True)(cmd)
                cmd = self.client.command(cmd)

                setattr(instance, method.replace('c_', ''), cmd)
            elif stw(method, 'e_'):
                setattr(instance, method.replace('e_', 'on_'), method)

        self.client.add_cog(instance)
        return True

    async def _load_ext(self, name, class_name, cxt):
        self.logger.info("load_ext: %s@%s", class_name, name)

        if name in NEW_BACKEND:
            return self.load_new_backend(name)


        # find/reload the module
        module = await self.get_module(name)
        if not module:
            self.logger.error("module not found/error loading module")
            return False

        # get the class that represents the module
        module_class = getattr(module, class_name, None)
        if not module_class:
            if cxt is not None:
                await cxt.say(":train:")
            self.logger.error("class instance is None")
            return False

        # instantiate and ext_load it
        instance = await self.mod_instance(name, module_class)
        if not instance: # catches False and None
            self.logger.error("instance isn't good")
            return False

        if name in self.modules:
            # delete old one
            del self.modules[name]

            # instiated with success, register all shit this module has
        ok = await self.register_mod(name, class_name, module, instance)
        if not ok:
            self.logger.error("Error registering module")
            return False

        # redo the event handler shit
        self.ev_empty()
        self.ev_load()

        # finally
        return True


    async def load_ext(self, name, class_name, cxt):
        # try
        ok = await self._load_ext(name, class_name, cxt)

        if ok:
            self.logger.info("Loaded %s", name)
            try:
                await cxt.say(":ok_hand:")
            except:
                pass
            return True
        else:
            self.logger.info("Error loading %s", name)
            try:
                await cxt.say(":poop:")
            except:
                sys.exit(0)
            return False

    async def c_reload(self, message, args, cxt):
        '''`j!reload module` - recarrega um módulo do josé'''
        await self.is_admin(message.author.id)

        if len(args) < 2:
            await cxt.say(self.c_reload.__doc__)
            return

        n = args[1]
        if n in self.modules:
            await self.load_ext(n, self.modules[n]['class'], cxt)
        else:
            await cxt.say("%s: module not found/loaded", (n,))

    async def c_unload(self, message, args, cxt):
        '''`j!unload module` - desrecarrega um módulo do josé'''
        await self.is_admin(message.author.id)

        if len(args) < 2:
            await cxt.say(self.c_reload.__doc__)
            return

        modname = args[1]

        if modname not in self.modules:
            await cxt.say("%s: module not loaded", (modname,))
        else:
            # unload it
            self.logger.info("!unload: %s" % modname)
            res = await self.unload_mod(modname)
            if res[0]:
                await cxt.say(":skull: `%s` is dead :skull:", (modname,))
            else:
                await cxt.say(":warning: Error happened: %s", (res[1],))

    async def c_loadmod(self, message, args, cxt):
        '''`j!loadmod class@module` - carrega um módulo do josé'''
        await self.is_admin(message.author.id)

        if len(args) < 2:
            await cxt.say(self.c_loadmod.__doc__)
            return

        # parse class@module
        modclass, modname = args[1].split('@')

        ok = await self.load_ext(modname, modclass, cxt)
        if ok:
            self.logger.info("!loadmod: %s" % modname)
            await cxt.say(":ok_hand: Success loading `%s`!", (modname,))
        else:
            await cxt.say(":warning: Error loading `%s` :warning:", (modname,))

    async def c_modlist(self, message, args, cxt):
        '''`j!modlist` - List loaded modules'''
        await cxt.say(self.codeblock("", " ".join(self.modules.keys())))

    async def c_hjose(self, message, args, cxt):
        await cxt.say(jcommon.JOSE_GENERAL_HTEXT, message.author)

    async def sec_auth(self, f, cxt):
        auth = await self.is_admin(cxt.message.author.id)
        if auth:
            self.command_lock = True
            await f(cxt)
        else:
            raise je.PermissionError()

    async def general_shutdown(self, cxt):
        self.made_gshutdown = True
        jcoin = self.modules['jcoin']['inst']
        josextra = self.modules['josextra']['inst']

        if cxt is not None:
            await jcoin.josecoin_save(cxt.message)
        else:
            await jcoin.josecoin_save(None)

        jcommon.log_channel_handler.in_shutdown()

        self.logger.info("%d messages in this session", josextra.total_msg)

        # unload all shit and shutdown.
        await self.unload_all()
        await self.client.logout()
        self.logger.info("Logged out")

    async def turnoff(self, cxt):
        self.logger.info("Turning Off from %s", str(cxt.message.author))

        josextra = self.modules['josextra']['inst']
        await cxt.say(":wave: My best showdown was %d msgs/minute, %d msgs/hour, recv %d messages", \
            (josextra.best_msg_minute, josextra.best_msg_hour, josextra.total_msg))
        await self.general_shutdown(cxt)

    async def update(self, cxt):
        self.logger.info("Update from %s", str(cxt.message.author))

        josextra = self.modules['josextra']['inst']
        shutdown_msg = (":wave: My best showdown was %d msgs/minute, %d msgs/hour, recv %d messages" % \
                    (josextra.best_msg_minute, josextra.best_msg_hour, josextra.total_msg))

        out = subprocess.check_output("git pull", shell=True, \
            stderr=subprocess.STDOUT)
        res = out.decode("utf-8")
        await cxt.say("`git pull`: ```%s```\n %s", (res, shutdown_msg))

        await self.general_shutdown(cxt)

    async def c_shutdown(self, message, args, cxt):
        '''`j!shutdown` - turns off josé'''
        await self.sec_auth(self.turnoff, cxt)

    async def c_update(self, message, args, cxt):
        '''`j!update` - Pulls from github and shutsdown'''
        await self.sec_auth(self.update, cxt)

    async def c_shell(self, message, args, cxt):
        '''`j!shell command` - execute shell commands'''
        await self.is_admin(cxt.message.author.id)

        command = ' '.join(args[1:])

        out = subprocess.check_output(command, shell=True, \
            stderr=subprocess.STDOUT)
        res = out.decode("utf-8")

        await cxt.say("`%s`: ```%s```\n", (command, res,))

    async def c_ping(self, message, args, cxt):
        '''`j!ping` - pong'''

        delta_cmd_process = (time.time() - cxt.t_creation) * 1000

        t_init = time.time()
        await cxt.send_typing()
        t_end = time.time()
        delta_typing = (t_end - t_init) * 1000

        t_init = time.time()
        pong = await cxt.say("Pong! `cmd_process`: **%.2fms**, `send_typing`: **%.2fms**", \
            (delta_cmd_process, delta_typing))
        t_end = time.time()

        delta_send_message = (t_end - t_init) * 1000
        await self.client.edit_message(pong, pong.content + \
            ", `send_message`: **%.2fms**" % (delta_send_message))

    async def c_rand(self, message, args, cxt):
        '''`j!rand min max` - gera um número aleatório no intervalo [min, max]'''
        n_min, n_max = 0,0
        try:
            n_min = int(args[1])
            n_max = int(args[2])
        except:
            await cxt.say("Error parsing numbers")
            return

        if n_min > n_max:
            await cxt.say("`min` > `max`, sorry")
            return

        n_rand = random.randint(n_min, n_max)
        await cxt.say("random number from %d to %d: %d", (n_min, n_max, n_rand))
        return

    async def c_pstatus(self, message, args, cxt):
        '''`j!pstatus` - muda o status do josé'''
        await self.is_admin(message.author.id)

        playing_name = ' '.join(args[1:])
        g = discord.Game(name=playing_name, url=playing_name)
        await self.client.change_presence(game=g)

    async def c_escolha(self, message, args, cxt):
        '''`j!escolha elemento1;elemento2;elemento3;...;elementon` - escolha.'''
        if len(args) < 2:
            await cxt.say(self.c_escolha.__doc__)
            return

        escolhas = (' '.join(args[1:])).split(';')
        choice = random.choice(escolhas)
        await cxt.say(">%s", (choice,))

    async def c_pick(self, message, args, cxt):
        '''`j!pick` - alias for `!escolha`'''
        await self.c_escolha(message, args, cxt)

    async def c_nick(self, message, args, cxt):
        '''`j!nick nickname` - splitted'''
        await cxt.say("Use `j!gnick` for global nickname change(you don't want that)\
use `j!lnick` for local nickname")

    async def c_gnick(self, message, args, cxt):
        '''`j!gnick [nick]` - only admins'''
        await self.is_admin(message.author.id)

        if len(args) < 2:
            await cxt.say(self.c_gnick.__doc__)
            return

        self.nick = ' '.join(args[1:])

        guilds = 0
        for server in self.client.servers:
            m = server.get_member(jcommon.JOSE_ID)
            await self.client.change_nickname(m, self.nick)
            guilds += 1

        await cxt.say("Changed nickname to `%r` in %d guilds", (self.nick, guilds))

    async def c_lnick(self, message, args, cxt):
        '''`j!lnick nick` - change josé\'s nickname for this server'''

        if len(args) < 2:
            await cxt.say(self.c_lnick.__doc__)
            return

        nick = ' '.join(args[1:])

        m = message.server.get_member(jcommon.JOSE_ID)
        await self.client.change_nickname(m, nick)
        await cxt.say("Nickname changed to `%r`", (nick,))

    async def c_version(self, message, args, cxt):
        pyver = '%d.%d.%d' % (sys.version_info[:3])
        head_id = subprocess.check_output("git rev-parse --short HEAD", \
            shell=True).decode('utf-8')

        await cxt.say("`José v%s git:%s py:%s d.py:%s`", (jcommon.JOSE_VERSION, \
            head_id, pyver, discord.__version__))

    async def c_jose_add(self, message, args, cxt):
        await cxt.say("José Add URL:\n```%s```", (jcommon.OAUTH_URL,))

    async def c_clist(self, message, args, cxt):
        '''`j!clist module` - mostra todos os comandos de tal módulo'''
        if len(args) < 2:
            await cxt.say(self.c_clist.__doc__)
            return

        modname = args[1]

        if modname not in self.modules:
            await cxt.say("`%s`: Not found", (modname,))
            return

        res = ' '.join(self.modules[modname]['methods'])
        res = res.replace('c_', jcommon.JOSE_PREFIX)
        await cxt.say(self.codeblock('', res))

    async def c_uptime(self, message, args, cxt):
        '''`j!uptime` - mostra o uptime do josé'''
        sec = (time.time() - self.start_time)
        MINUTE  = 60
        HOUR    = MINUTE * 60
        DAY     = HOUR * 24

        days    = int(sec / DAY)
        hours   = int((sec % DAY) / HOUR)
        minutes = int((sec % HOUR) / MINUTE)
        seconds = int(sec % MINUTE)

        fmt = "`Uptime: %d days, %d hours, %d minutes, %d seconds`"
        await cxt.say(fmt % (days, hours, minutes, seconds))

    async def c_eval(self, message, args, cxt):
        # eval expr
        await self.is_admin(message.author.id)

        eval_cmd = ' '.join(args[1:])
        if eval_cmd[0] == '`' and eval_cmd[-1] == '`':
            eval_cmd = eval_cmd[1:-1]

        self.logger.info("%s[%s] is EVALing %r", message.author, \
            message.author.id, eval_cmd)

        res = eval(eval_cmd)
        await cxt.say("```%s``` -> `%s`", (eval_cmd, res))

    async def c_rplaying(self, message, args, cxt):
        await self.is_admin(message.author.id)

        # do the same thing again
        playing_phrase = random.choice(jcommon.JOSE_PLAYING_PHRASES)
        playing_name = '%s | v%s | %d guilds | %shjose' % (playing_phrase, jcommon.JOSE_VERSION, \
            len(self.client.servers), jcommon.JOSE_PREFIX)
        self.logger.info("Playing %s", playing_name)
        g = discord.Game(name = playing_name, url = playing_name)
        await self.client.change_presence(game = g)

    async def c_tempadmin(self, message, args, cxt):
        '''`j!tempadmin userID` - maka a user an admin until josé restarts'''
        await self.is_admin(message.author.id)

        try:
            userid = args[1]
        except Exception as e:
            await cxt.say(repr(e))
            return

        jcommon.ADMIN_IDS.append(userid)
        if userid in jcommon.ADMIN_IDS:
            await cxt.say(":cop: Added `%r` as temporary admin!", (userid,))
        else:
            await cxt.say(":poop: Error adding user as temporary admin")

    async def c_username(self, message, args, cxt):
        '''`j!username` - change josé username'''
        await self.is_admin(message.author.id)

        try:
            name = str(args[1])
            await self.client.edit_profile(username=name)
            await cxt.say("done!!!!1!!1 i am now %s", (name,))
        except Exception as e:
            await cxt.say(":thinking: %r", (e,))

    async def c_announce(self, message, args, cxt):
        '''`j!announce` - announce stuff'''
        await self.is_admin(message.author.id)

        announcement = ' '.join(args[1:])
        await cxt.say("I'm gonna say `\n%r\n` to all servers I'm in, are you \
sure about that, pretty admin? (y/n)", (announcement,))
        yesno = await self.client.wait_for_message(author=message.author)

        if yesno.content == 'y':
            svcount, chcount = 0, 0
            for server in self.client.servers:
                for channel in server.channels:
                    if channel.is_default:
                        await self.client.send_message(channel, announcement)
                        chcount += 1
                svcount += 1
            await cxt.say(":cop: Sent announcement to \
%d servers, %d channels", (svcount, chcount))
        else:
            await cxt.say("jk I'm not gonna do what you \
don't want (unless I'm skynet)")

    async def c_gcollect(self, message, args, cxt):
        await self.is_admin(message.author.id)
        obj = gc.collect()
        await cxt.say(":cop: Collected %d objects!", (obj,))

    async def c_listev(self, message, args, cxt):
        res = []
        for evname in sorted(self.event_tbl):
            evcount = len(self.event_tbl[evname])
            res.append('event %r : %d handlers' % (evname, evcount))

        await cxt.say(":cop: There are %d registered events: ```%s```" % \
            (len(self.event_tbl), '\n'.join(res)))

    async def c_logs(self, message, args, cxt):
        '''`j!logs num` - get `num` last lines from `José.log`'''
        await self.is_admin(message.author.id)

        try:
            linestoget = int(args[1])
        except IndexError:
            await cxt.say("use the command fucking properly")
            return
        except Exception as e:
            await cxt.say(":warning: %r" % e)
            return

        cmd = "cat José.log | tail -%d" % (linestoget)
        res = subprocess.check_output(cmd, shell=True, \
            stderr=subprocess.STDOUT)
        res = res.decode("utf-8")

        await cxt.say("Last `%d` lines from José.log said: \n```%s```" % \
            (linestoget, res))

    async def c_sysping(self, message, args, cxt):
        '''`j!sysping host` - ping from josebox'''
        await self.is_admin(message.author.id)

        if len(args) < 1:
            await cxt.say(self.c_sysping.__doc__)
            return

        host = ' '.join(args[1:])

        ping = subprocess.Popen(
            ["ping", "-c", "2", host],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )

        _out, _error = ping.communicate()
        out = self.codeblock("", _out.decode('utf-8'))
        error = self.codeblock("", _error.decode('utf-8'))

        await cxt.say("OUT:%s\nERR:%s", (out, error))

    async def c_mode(self, message, args, cxt):
        '''`j!mode normal|dev` - change jose mode'''
        await self.is_admin(message.author.id)

        if len(args) < 1:
            await cxt.say(self.c_mode.__doc__)
            return

        mode = args[1]

        if mode == 'normal':
            self.dev_mode = False
        elif mode == 'dev':
            self.dev_mode = True
            await self.do_dev_mode()

        await cxt.say("mode changed to `%r`", (mode,))

    async def c_blockserver(self, message, args, cxt):
        '''`j!blockserver serverid` - Blocks/Unblocks a server from message processing.'''
        await self.is_admin(message.author.id)

        if len(args) < 2:
            await cxt.say(self.c_blockserver.__doc__)
            return

        guild_id = args[1]
        guild = self.client.get_server(guild_id)

        if guild is None:
            await cxt.say("Guild not found, are you sure José is in it?")
            return

        guild_name = guild.name

        if guild_id in self.blocks['guilds']:
            # remove from blocks
            self.blocks['guilds'].remove(guild_id)
            self.logger.info("Unblocked guild %s, %s", guild_name, guild_id)
            await cxt.say("Unblocked guild `%s[%s]`.", (guild_name, guild_id,))
        else:
            self.blocks['guilds'].append(guild_id)
            self.logger.info("Blocked guild %s, %s", guild_name, guild_id)
            await cxt.say("Blocked guild `%s[%s]`.", (guild_name, guild_id,))

        self.jsondb_save('blocks')

    async def c_blockuser(self, message, args, cxt):
        '''`j!blockuser userid` - Blocks/Unblocks an User from message processing.'''
        await self.is_admin(message.author.id)

        if len(args) < 2:
            await cxt.say(self.c_blockuser.__doc__)
            return

        user_id = args[1]
        user = discord.utils.get(self.client.get_all_members(), id = user_id)

        if user is None:
            await cxt.say("User not found")
            return

        if user_id in self.blocks['users']:
            # remove from blocks
            self.blocks['users'].remove(user_id)
            self.logger.info("Unblocked user %s, %s", user, user_id)
            await cxt.say("Unblocked user `%s[%s]`.", (user, user_id,))
        else:
            self.blocks['users'].append(user_id)
            self.logger.info("Blocked user %s, %s", user, user_id)
            await cxt.say("Blocked user `%s[%s]`.", (user, user_id,))

        self.jsondb_save('blocks')
