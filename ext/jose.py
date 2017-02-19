import discord
import asyncio

import sys
import time
from random import SystemRandom
random = SystemRandom()

import base64
import subprocess

import aiohttp
import urllib.parse
import urllib.request
import re
import json
import importlib
import copy

sys.path.append("..")
import josecommon as jcommon
import joseerror as je
import joseconfig as jconfig
import jcoin.josecoin as jcoin

jose_debug = jcommon.jose_debug

class JoseBot(jcommon.Extension):
    def __init__(self, cl):
        jcommon.Extension.__init__(self, cl)
        self.nick = 'jose-bot'
        self.modules = {}
        self.env = {
            'cooldowns': {},
            'stcmd': {},
        }
        self.start_time = time.time()
        self.command_lock = False
        self.ev_empty()

    def ev_empty(self):
        self.event_tbl = {
            'on_message': [],
            'any_message': [],
        }

    def ev_load(self):
        # register events
        for modname in self.modules:
            module = self.modules[modname]
            modinst = self.modules[modname]['inst']
            for method in module['handlers']:
                if method.startswith("e_"):
                    evname = method[method.find("_")+1:]
                    jcommon.logger.info("Register Event %s@%s:%s", \
                        method, modname, evname)

                    # check if event exists
                    if evname in self.event_tbl:
                        handler = getattr(modinst, method, None)
                        if handler is None:
                            # ????
                            jcommon.logger.error("Event handler %s@%s:%s doesn't... exist????", \
                                method, modname, evname)
                            sys.exit(0)

                        self.event_tbl[evname].append(handler)
                    else:
                        jcommon.logger.warning("Event %s@%s:%s doesn't exist in Event Table", \
                            method, modname, evname)

    async def unload_mod(self, modname):
        module = self.modules[modname]
        # if ext_unload exists
        if getattr(module['inst'], 'ext_unload', False):
            try:
                ok = await module['inst'].ext_unload()
                # delete stuff from the module table
                del self.modules[modname]
                return ok
            except Exception as e:
                self.logger.error("%s[ERROR]: %s" % (modname, repr(e)))
                return False, repr(e)
        else:
            self.logger.info("%s doesn't have ext_unload", modname)
            return False, "ext_unload isn't available in %s" % (modname)

    async def unload_all(self):
        # unload all modules
        to_remove = self.modules.keys()

        count = 0
        for modname in to_remove:
            ok = await self.unload_mod(modname)
            if not ok:
                return ok
            count += 1

        self.logger.info("[unload_all] Unloaded %d out of %d modules", \
            count, len(to_remove))

        return True, ''

    def load_gext(self, inst, n):
        self.logger.info("Loading gext %s", n)
        methods = (method for method in dir(inst) if callable(getattr(inst, method)))

        self.modules[n] = {'inst': inst, 'methods': [], 'handlers': [], 'class': ''}

        for method in methods:
            if method.startswith('c_'):
                self.logger.debug("add %s", method)
                setattr(self, method, getattr(inst, method))
                self.modules[n]['methods'].append(method)

        self.logger.info("Loaded gext %s", n)
        return True

    async def get_module(self, name):
        if name in self.modules:
            # Already loaded module, unload it

            mod = self.modules[name]
            try:
                ok = await mod['inst'].ext_unload()
                if not ok[0]:
                    self.logger.error("Error on ext_unload(%s): %s", name, ok[1])
                    sys.exit(0)
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
        mod_ext_load = getattr(instance, 'ext_load', False)
        if not mod_ext_load:
            # module not compatible with API
            self.logger.error("Module not compatible with EAPI")
            return False
        else:
            # hey thats p good
            try:
                ok = await instance.ext_load()
                if not ok[0]:
                    self.logger.error("Error happened on ext_load(%s): %s", name, ok[1])
                    sys.exit(0)
                else:
                    return instance
            except Exception as e:
                self.logger.warn("Almost loaded %s: %s", name, repr(e))
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
                self.logger.debug("EAPI command %s", method)
                setattr(self, method, getattr(instance, method))
                methods.append(method)

            elif stw(method, 'e_'):
                # Event handler
                self.logger.debug("EAPI ev handler %s", method)
                handlers.append(method)

        # copy them and kill them
        ref['methods'] = copy.copy(methods)
        ref['handlers'] = copy.copy(handlers)
        del methods, handlers

        # done
        return True

    async def _load_ext(self, name, class_name, cxt):
        self.logger.info("load_ext: %s@%s", class_name, name)

        # find/reload the module
        module = await self.get_module(name)
        if not module:
            self.logger.error("module not found/error loading module")
            return False

        # get the class that represents the module
        module_class = getattr(module, class_name, None)
        if module_class is None:
            if cxt is not None:
                await cxt.say(":train:")
            self.logger.error("class instance is None")
            return False

        # instantiate and ext_load it
        instance = await self.mod_instance(name, module_class)
        if instance is None:
            self.logger.error("instance is None")
            return False

        if name in self.modules:
            # delete old one
            del self.modules[name]

        # instiated with success, register all shit this module has
        ok = await self.register_mod(name, class_name, module, instance)
        if not ok:
            self.logger.error("Error registering module")
            return False

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
        else:
            self.logger.info("Error loading %s", name)
            try:
                await cxt.say(":poop:")
            except:
                sys.exit(0)

    async def mod_recv(self, message):
        await self.recv(message)
        for module in list(self.modules.values()):
            await module['inst'].recv(message)

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
            await cxt.say(self.c_reload.__doc__)
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
        '''`j!modlist` - Módulos do josé'''
        mod_list = []
        for key in self.modules:
            if 'module' in self.modules[key]:
                # normally loaded ext, can use !reload on it
                mod_list.append(key)
            else:
                # externally loaded ext, can't reload
                mod_list.append('gext:%s' % key)

        # show everyone in a nice codeblock
        await cxt.say(self.codeblock("", " ".join(mod_list)))

    def says(self, msg):
        # calls self.say but in an non-async context
        asyncio.ensure_future(self.say(msg), loop=self.loop)

    async def c_hjose(self, message, args, cxt):
        await cxt.say(jcommon.JOSE_GENERAL_HTEXT, message.author)

    async def sec_auth(self, f, cxt):
        auth = await self.is_admin(self.current.author.id)
        if auth:
            self.command_lock = True
            await f(cxt)
            self.command_lock = False
        else:
            raise je.PermissionError()

    async def turnoff(self, cxt):
        await jcoin.JoseCoin(self.client).josecoin_save(self.current, True)
        await self.unload_all()
        await cxt.say(":wave: kthxbye :wave:")
        await self.client.logout()
        sys.exit(0)

    async def c_shutdown(self, message, args, cxt):
        '''`j!shutdown` - desliga o josé'''
        await self.sec_auth(self.turnoff, cxt)

    async def c_ping(self, message, args, cxt):
        '''`j!ping` - pong'''
        t_init = time.time()
        t_cmdprocess = (time.time() - cxt.t_creation) * 1000
        pong = await cxt.say("pong! took **%.2fms** to process the command", (t_cmdprocess,))
        t_end = time.time()
        delta = t_end - t_init
        await self.client.edit_message(pong, pong.content + ", **%.2fms** to send it" % (delta * 1000))

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

    async def c_enc(self, message, args, cxt):
        '''`j!enc text` - encriptar'''
        if len(args) < 2:
            await cxt.say(self.c_enc.__doc__)
            return

        to_encrypt = ' '.join(args[1:])
        encdata = await jcommon.str_xor(to_encrypt, jcommon.JCRYPT_KEY)
        a85data = base64.a85encode(bytes(encdata, 'UTF-8'))
        await cxt.say('resultado(enc): %s', (a85data.decode('UTF-8'),))
        return

    async def c_dec(self, message, args, cxt):
        '''`j!dec text` - desencriptar'''
        if len(args) < 2:
            await cxt.say(self.c_dec.__doc__)
            return

        to_decrypt = ' '.join(args[1:])
        to_decrypt = to_decrypt.encode('UTF-8')
        try:
            to_decrypt = base64.a85decode(to_decrypt).decode('UTF-8')
        except Exception as e:
            await cxt.say("dec: erro tentando desencodar a mensagem(%r)", (e,))
            return
        plaintext = await jcommon.str_xor(to_decrypt, jcommon.JCRYPT_KEY)
        await cxt.say("resultado(dec): %s", (plaintext,))
        return

    async def c_money(self, message, args, cxt):
        '''`j!money quantity base to` - converte dinheiro usando cotações etc
        `!money list` - lista todas as moedas disponíveis'''

        if len(args) > 1:
            if args[1] == 'list':
                r = await aiohttp.request('GET', "http://api.fixer.io/latest")
                content = await r.text()
                data = json.loads(content)
                await cxt.say(self.codeblock("", " ".join(data["rates"])))
                return

        if len(args) < 3:
            await cxt.say(self.c_money.__doc__)
            return

        try:
            amount = float(args[1])
        except Exception as e:
            await cxt.say("Error parsing `quantity`")
            return

        currency_from = args[2]
        currency_to = args[3]

        url = "http://api.fixer.io/latest?base={}".format(currency_from.upper())
        r = await aiohttp.request('GET', url)
        content = await r.text()
        data = json.loads(content)

        if 'error' in data:
            await cxt.say("!money: %s", (data['error'],))
            return

        if currency_to not in data['rates']:
            await cxt.say("Invalid currency to convert to")
            return

        rate = data['rates'][currency_to]
        res = amount * rate

        await cxt.say('{} {} = {} {}'.format(
            amount, currency_from, res, currency_to
        ))

    async def c_yt(self, message, args, cxt):
        '''`j!yt [termo 1] [termo 2]...` - procura no youtube'''
        if len(args) < 2:
            await cxt.say(self.c_yt.__doc__)
            return

        search_term = ' '.join(args[1:])

        loop = asyncio.get_event_loop()

        self.logger.info("Youtube request @ %s : %s", message.author, search_term)

        query_string = urllib.parse.urlencode({"search_query" : search_term})

        url = "http://www.youtube.com/results?" + query_string
        future_search = loop.run_in_executor(None, urllib.request.urlopen, url)
        html_content = await future_search

        future_re = loop.run_in_executor(None, re.findall, r'href=\"\/watch\?v=(.{11})', html_content.read().decode())
        search_results = await future_re

        if len(search_results) < 2:
            await cxt.say("!yt: Nenhum resultado encontrado.")
            return

        await cxt.say("http://www.youtube.com/watch?v=" + search_results[0])

    async def c_sndc(self, message, args, cxt):
        '''`j!sndc [termo 1] [termo 2]...` - procura no soundcloud'''
        if len(args) < 2:
            await cxt.say(self.c_sndc.__doc__)
            return

        query = ' '.join(args[1:])

        self.logger.info("Soundcloud request: %s", query)

        if len(query) < 3:
            await cxt.say("preciso de mais coisas para pesquisar(length < 3)")
            return

        search_url = 'https://api.soundcloud.com/search?q=%s&facet=model&limit=10&offset=0&linked_partitioning=1&client_id='+jconfig.soundcloud_id
        url = search_url % urllib.parse.quote(query)

        while url:
            response = await aiohttp.request('GET', url)

            if response.status != 200:
                await cxt.say("!sndc: error: status code != 200(st = %d)", (response.status))
                return

            try:
                doc = await response.json()
            except Exception as e:
                await jose_debug(message, "!sndc: py_err %s" % str(e))
                return

            for entity in doc['collection']:
                if entity['kind'] == 'track':
                    await cxt.say(entity['permalink_url'])
                    return

            await cxt.say("verifique sua pesquisa, porque nenhuma track foi encontrada.")
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
        '''`j!nick [nick]` - [SOMENTE ADMIN]'''
        await self.is_admin(message.author.id)

        if len(args) < 2:
            self.nick = 'josé'
        else:
            self.nick = ' '.join(args[1:])

        if message.server is None:
            for s in self.client.servers:
                m = s.get_member(jcommon.JOSE_ID)
                await self.client.change_nickname(m, self.nick)
        else:
            m = message.server.get_member(jcommon.JOSE_ID)
            await self.client.change_nickname(m, self.nick)

        return

    async def c_distatus(self, message, args, cxt):
        '''`j!distatus` - mostra alguns dados para mostrar se o Discord está funcionando corretamente'''
        await self.is_admin(message.author.id)

        host = "discordapp.com"

        ping = subprocess.Popen(
            ["ping", "-c", "6", host],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )

        out, error = ping.communicate()
        matcher = re.compile("rtt min/avg/max/mdev = (\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)")
        rtt = matcher.search(out.decode('utf-8')).groups()

        fmt = 'resultados de ping para `%s` min `%sms` avg `%sms` max `%sms` mdev `%sms`\n%s'
        looks_like = ''
        if float(rtt[1]) > 100:
            looks_like = 'Parece que algo tá rodando ruim nos servidores, cheque http://status.discordapp.com'
        elif float(rtt[2]) > 150:
            looks_like = 'Alguma coisa deve ter ocorrido no meio dos pings, tente denovo'
        else:
            looks_like = 'Tudo bem... eu acho'

        await cxt.say(fmt % (host, rtt[0], rtt[1], rtt[2], rtt[3], looks_like))

    async def c_version(self, message, args, cxt):
        '''`j!version` - mostra a versão do jose'''
        pyver = '%d.%d.%d' % (sys.version_info[:3])
        await cxt.say("`José v%s py:%s discord.py:%s`", (jcommon.JOSE_VERSION
            , pyver, discord.__version__))

    async def c_jose_add(self, message, args, cxt):
        await cxt.say("José pode ser adicionado para outro servidor usando este link:\n```%s```", (jcommon.OAUTH_URL,))

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

        fmt = "`Uptime: %d dias, %d horas, %d minutos, %d segundos`"
        await cxt.say(fmt % (days, hours, minutes, seconds))

    async def c_eval(self, message, args, cxt):
        # eval expr
        await self.is_admin(message.author.id)

        eval_cmd = ' '.join(args[1:])
        if eval_cmd[0] == '`' and eval_cmd[-1] == '`':
            eval_cmd = eval_cmd[1:-1]

        res = eval(eval_cmd)
        await cxt.say("```%s``` -> `%s`", (eval_cmd, res))

    async def c_rplaying(self, message, args, cxt):
        await self.is_admin(message.author.id)

        # do the same thing again
        playing_phrase = random.choice(jcommon.JOSE_PLAYING_PHRASES)
        playing_name = '%s | v%s | %d guilds | %shjose' % (playing_phrase, jcommon.JOSE_VERSION, \
            len(self.client.servers), jcommon.JOSE_PREFIX)
        jcommon.logger.info("Playing %s", playing_name)
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
            await cxt.say("Added `%r` as temporary admin!", (userid,))
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
            await cxt.say("err hapnnd!!!!!!!! %r", (e,))

    async def c_announce(self, message, args, cxt):
        '''`j!announce` - announce stuff'''
        await self.is_admin(message.author.id)

        announcement = ' '.join(args[1:])
        await cxt.say("I'm gonna say `%r` to all servers I'm in, are you \
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
            await cxt.say("Sent announcement to \
%d servers, %d channels", (svcount, chcount))
        else:
            await cxt.say("jk I'm not gonna do what you \
don't want (unless I'm skynet)")
