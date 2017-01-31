import discord
import asyncio

import sys
import time
import os
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
            'spam': {},
            'spamcl': {},
        }
        self.start_time = time.time()
        self.command_lock = False
        self.queue = []

    async def unload_all(self):
        # unload all modules
        for modname in self.modules:
            module = self.modules[modname]
            # if ext_unload exists
            if getattr(module['inst'], 'ext_unload', False):
                try:
                    ok = await module['inst'].ext_unload()
                    if not ok[0]:
                        self.logger.error("Error happened when ext_unload(%s): %s", modname, ok[1])
                    else:
                        self.logger.info("Unloaded %s", modname)
                except Exception as e:
                    self.logger.warn("Almost unloaded %s: %s", modname, repr(e))
            else:
                self.logger.info("%s doesn't have ext_unload", modname)

        self.logger.info("Unloaded all modules")

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

    async def load_ext(self, n, n_cl, cxt):
        loaded_success = False
        loaded_almost = False

        self.logger.info("load_ext: %s@%s", n_cl, n)
        module = None
        if n in self.modules: #already loaded
            try:
                ok = await self.modules[n]['inst'].ext_unload()
                if not ok[0]:
                    self.logger.error("Error happened on ext_unload(%s): %s", n, ok[1])
                    sys.exit(0)
            except Exception as e:
                self.logger.warn("Almost unloaded %s: %s", n, repr(e))
                loaded_almost = True

            # reimport
            module = importlib.reload(self.modules[n]['module'])
        else:
            module = importlib.import_module('ext.%s' % n)

        # instantiate from module
        cl_inst = getattr(module, n_cl, None)
        if cl_inst is None:
            if self.current is not None:
                await cxt.say(":train:")
            self.logger.error("cl_inst = None")
            loaded_success = False
            loaded_almost = True

        inst = None
        if cl_inst is not None:
            inst = cl_inst(self.client)

        try:
            # try to ext_load it
            ok = await inst.ext_load()
            if not ok[0]:
                self.logger.error("Error happened on ext_load(%s): %s", n, ok[1])
                sys.exit(0)
        except Exception as e:
            self.logger.warn("Almost loaded %s: %s", n, repr(e))
            loaded_almost = True

        # if instantiated, register the commands and events
        if inst is not None:
            methods = (method for method in dir(inst) if callable(getattr(inst, method)))
            self.modules[n] = {
                'inst': inst,
                'methods': [],
                'class': n_cl,
                'module': module,
                'handlers': []
            }

            for method in methods:
                if method.startswith('c_'):
                    self.logger.debug("add %s", method)
                    setattr(self, method, getattr(inst, method))
                    self.modules[n]['methods'].append(method)
                    loaded_success = True
                elif method.startswith('e_'):
                    self.logger.debug("handler %s" % method)
                    self.modules[n]['handlers'].append(method)
                    loaded_success = True

        if cxt is not None:
            if loaded_success:
                await cxt.say(":ok_hand:")
                return True
            elif loaded_almost:
                await cxt.say(":train:")
                return False
            else:
                await cxt.say(":poop:")
                return False
        else:
            if not loaded_success:
                self.logger.error("Error loading %s", n)
                sys.exit(0)

            if loaded_almost:
                self.logger.error("Almost loaded %s", n)
                sys.exit(0)
            self.logger.info("Loaded %s" % n)

    async def mod_recv(self, message):
        await self.recv(message)
        for module in list(self.modules.values()):
            await module['inst'].recv(message)

    async def c_reload(self, message, args, cxt):
        '''`!reload module` - recarrega um módulo do josé'''
        await self.is_admin(message.author.id)

        if len(args) < 2:
            await cxt.say(self.c_reload.__doc__)
            return

        n = args[1]
        if n in self.modules:
            await self.load_ext(n, self.modules[n]['class'], cxt)
        else:
            await cxt.say("%s: module not found/loaded" % n)

    async def c_unload(self, message, args, cxt):
        '''`!unload module` - desrecarrega um módulo do josé'''
        await self.is_admin(message.author.id)

        if len(args) < 2:
            await cxt.say(self.c_reload.__doc__)
            return

        modname = args[1]

        if modname not in self.modules:
            await cxt.say("%s: module not loaded" % modname)
        else:
            # unload it
            self.logger.info("!unload: %s" % modname)
            res = await self.unload_mod(modname)
            if res[0]:
                await cxt.say(":skull: `%s` is dead :skull:" % modname)
            else:
                await cxt.say(":warning: Error happened: %s" % res[1])

    async def c_loadmod(self, message, args, cxt):
        '''`!loadmod class@module` - carrega um módulo do josé'''
        await self.is_admin(message.author.id)

        if len(args) < 2:
            await cxt.say(self.c_reload.__doc__)
            return

        # parse class@module
        modclass, modname = args[1].split('@')

        ok = await self.load_ext(modname, modclass, cxt)
        if ok:
            self.logger.info("!loadmod: %s" % modname)
            await cxt.say(":ok_hand: Success loading `%s`!" % modname)
        else:
            await cxt.say(":warning: Error loading `%s` :warning:" % modname)

    async def c_modlist(self, message, args, cxt):
        '''`!modlist` - Módulos do josé'''
        mod_gen = (key for key in self.modules)
        mod_generator = []
        for key in mod_gen:
            if 'module' in self.modules[key]:
                # normally loaded ext, can use !reload on it
                mod_generator.append('ext:%s' % key)
            else:
                # externally loaded ext, can't reload
                mod_generator.append('gext:%s' % key)
        await cxt.say("módulos carregados: %s" % (" ".join(mod_generator)))

    def says(self, msg):
        # calls self.say but in an non-async context
        asyncio.ensure_future(self.say(msg), loop=self.loop)

    async def c_htjose(self, message, args, cxt):
        await cxt.say(jcommon.JOSE_HELP_TEXT, channel=message.author)

    async def c_htgeral(self, message, args, cxt):
        await cxt.say(jcommon.JOSE_GENERAL_HTEXT, channel=message.author)

    async def c_httech(self, message, args, cxt):
        await cxt.say(jcommon.JOSE_TECH_HTEXT, channel=message.author)

    async def sec_auth(self, f, cxt):
        auth = await self.is_admin(self.current.author.id)
        if auth:
            self.command_lock = True
            await f(cxt)
            self.command_lock = False
        else:
            await self.debug("*PermError*: sem permissão")

    async def turnoff(self, cxt):
        await jcoin.JoseCoin(self.client).josecoin_save(self.current, True)
        await self.unload_all()
        await cxt.say(":wave: kthxbye :wave:")
        await self.client.logout()
        sys.exit(0)

    async def reboot(self, cxt):
        await jcoin.JoseCoin(self.client).josecoin_save(self.current, True)
        await self.unload_all()
        await self.client.logout()
        os.system("./reload_jose.sh &")
        sys.exit(0)

    async def update(self, cxt):
        banner = "atualizando josé para nova versão(versão antiga: %s)" % (jcommon.JOSE_VERSION)
        await self.debug(banner)
        await jcoin.JoseCoin(self.client).josecoin_save(self.current, True)
        await self.client.logout()
        os.system("./reload_jose.sh &")
        sys.exit(0)

    async def c_shutdown(self, message, args, cxt):
        '''`!shutdown` - desliga o josé'''
        await self.sec_auth(self.turnoff, cxt)

    async def c_reboot(self, message, args, cxt):
        '''`!reboot` - reinicia o josé'''
        #await self.sec_auth(self.reboot)
        pass

    async def c_update(self, message, args, cxt):
        '''`!update` - atualiza o josé'''
        #await self.sec_auth(self.update)
        pass

    async def c_ping(self, message, args, cxt):
        '''`!ping` - pong'''
        t_init = time.time()
        pong = await cxt.say("pong")
        t_end = time.time()
        delta = t_end - t_init
        await self.client.edit_message(pong, "pong, **%.2fms**" % (delta * 100))

    async def c_rand(self, message, args, cxt):
        '''`!rand min max` - gera um número aleatório no intervalo [min, max]'''
        n_min, n_max = 0,0
        try:
            n_min = int(args[1])
            n_max = int(args[2])
        except:
            await self.debug("erro parseando os números para a função.")
            return

        if n_min > n_max:
            await self.debug("minimo > máximo, intervalo não permitido")
            return

        n_rand = random.randint(n_min, n_max)
        await cxt.say("Número aleatório de %d a %d: %d" % (n_min, n_max, n_rand))
        return

    async def c_enc(self, message, args, cxt):
        '''`!enc text` - encriptar'''
        if len(args) < 2:
            await cxt.say(self.c_enc.__doc__)
            return

        to_encrypt = ' '.join(args[1:])
        encdata = await jcommon.str_xor(to_encrypt, jcommon.JCRYPT_KEY)
        a85data = base64.a85encode(bytes(encdata, 'UTF-8'))
        await cxt.say('resultado(enc): %s' % a85data.decode('UTF-8'))
        return

    async def c_dec(self, message, args, cxt):
        '''`!dec text` - desencriptar'''
        if len(args) < 2:
            await cxt.say(self.c_dec.__doc__)
            return

        to_decrypt = ' '.join(args[1:])
        to_decrypt = to_decrypt.encode('UTF-8')
        try:
            to_decrypt = base64.a85decode(to_decrypt).decode('UTF-8')
        except Exception as e:
            await cxt.say("dec: erro tentando desencodar a mensagem(%r)" % e)
            return
        plaintext = await jcommon.str_xor(to_decrypt, jcommon.JCRYPT_KEY)
        await cxt.say("resultado(dec): %s" % plaintext)
        return

    async def c_money(self, message, args, cxt):
        '''`!money quantity from to` - converte dinheiro usando cotações etc
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
            await self.debug("!money: %s" % data['error'])
            return

        rate = data['rates'][currency_to]
        res = amount * rate

        await cxt.say('{} {} = {} {}'.format(
            amount, currency_from, res, currency_to
        ))

    async def c_yt(self, message, args, cxt):
        '''`!yt [termo 1] [termo 2]...` - procura no youtube'''
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
            await client.send_message(message.channel, "!yt: Nenhum resultado encontrado.")
            return

        await cxt.say("http://www.youtube.com/watch?v=" + search_results[0])

    async def c_sndc(self, message, args, cxt):
        '''`!sndc [termo 1] [termo 2]...` - procura no soundcloud'''
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
                await self.debug("!sndc: error: status code != 200(st = %d)" % response.status)
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
        '''`!pstatus` - muda o status do josé'''
        await self.is_admin(message.author.id)

        playing_name = ' '.join(args[1:])
        g = discord.Game(name=playing_name, url=playing_name)
        await self.client.change_presence(game=g)

    async def c_fullwidth(self, message, args, cxt):
        '''`!fullwidth text` - ｆｕｌｌｗｉｄｔｈ　ｃｈａｒａｃｔｅｒｓ'''
        if len(args) < 2:
            await cxt.say("Nada de mensagem vazia")
            return

        ascii_text = ' '.join(args[1:])
        res = ascii_text.translate(jcommon.ascii_to_wide)
        await cxt.say(res)

    async def c_escolha(self, message, args, cxt):
        '''`!escolha elemento1;elemento2;elemento3;...;elementon` - escolha.'''
        if len(args) < 2:
            await cxt.say(self.c_escolha.__doc__)
            return

        escolhas = (' '.join(args[1:])).split(';')
        choice = random.choice(escolhas)
        await cxt.say("Eu escolho %s" % choice)

    async def c_nick(self, message, args, cxt):
        '''`!nick [nick]` - [SOMENTE ADMIN]'''
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
        '''`!distatus` - mostra alguns dados para mostrar se o Discord está funcionando corretamente'''
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
        '''`!version` - mostra a versão do jose'''
        pyver = '%d.%d.%d' % (sys.version_info[:3])
        await cxt.say("`José v%s py:%s discord.py:%s`" % (jcommon.JOSE_VERSION
            , pyver, discord.__version__))

    async def c_jose_add(self, message, args, cxt):
        await cxt.say("José pode ser adicionado para outro servidor usando este link:\n```%s```" % jcommon.OAUTH_URL)

    async def c_clist(self, message, args, cxt):
        '''`!clist module` - mostra todos os comandos de tal módulo'''
        if len(args) < 2:
            await cxt.say(self.c_clist.__doc__)
            return

        modname = args[1]

        if modname not in self.modules:
            await cxt.say("`%s`: Módulo não encontrado")
            return

        res = ' '.join(self.modules[modname]['methods'])
        res = res.replace('c_', '!')
        await cxt.say(self.codeblock('', res))

    async def c_uptime(self, message, args, cxt):
        '''`!uptime` - mostra o uptime do josé'''
        sec = (time.time() - self.start_time)
        MINUTE  = 60
        HOUR    = MINUTE * 60
        DAY     = HOUR * 24

        days    = int(sec / DAY)
        hours   = int((sec % DAY) / HOUR)
        minutes = int((sec % HOUR) / MINUTE)
        seconds = int(sec % MINUTE)

        fmt = "uptime: %d dias, %d horas, %d minutos, %d segundos"
        await self.debug(fmt % (days, hours, minutes, seconds))

    async def c_eval(self, message, args, cxt):
        # eval expr
        await self.is_admin(message.author.id)

        eval_cmd = ' '.join(args[1:])
        if eval_cmd[0] == '`' and eval_cmd[-1] == '`':
            eval_cmd = eval_cmd[1:-1]

        res = eval(eval_cmd)
        await cxt.say("```%s``` -> `%s`" % (eval_cmd, res))
