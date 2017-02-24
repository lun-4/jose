#!/usr/bin/env python3

import asyncio
import sys
from random import SystemRandom
random = SystemRandom()
import pickle

import discord

sys.path.append("..")
import josecommon as jcommon
import joseerror as je

import re
import io
import aiohttp
import urllib
import json

RI_TABLE = {
    '0': ':zero:',
    '1': ':one:',
    '2': ':two:',
    '3': ':three:',
    '4': ':four:',
    '5': ':five:',
    '6': ':six:',
    '7': ':seven:',
    '8': ':eight:',
    '9': ':nine:',

    '.': ':record_button:',
    '!': ':exclamation:',
    '?': ':question:',
    '+': ':heavy_plus_sign:',
    '-': ':heavy_minus_sign:',
}

MEMES_TECH_HELP = '''
Então você teve problemas usando `j!m stat` ou `j!m get` ou alguma merda assim?
Siga esses passos:
    1) Rode um `j!m check` no josé
        O `j!m check` irá checar meme por meme e ver se ele faz sentido, tipo ter um
        número de usos, se não, ele irá corrigir automaticamente

        Outra coisa que o `j!m check` faz é procurar por duplicatas, ou seja, 2 memes que
        vão pro mesmo resultado, ele te mostra quem tem duplicata e você remove manualmente
    2) Se o problema persiste, fale com lunão.
'''

BLACK_MIRROR_MESSAGES = [
    'http://s2.glbimg.com/beSMsXdBIPHqeQxdWi-nM31wNXs=/s.glbimg.com/jo/eg/f/original/2016/11/18/fdsaff.jpg',
    'http://s2.glbimg.com/N8LLtE22ZW2pFjlhzQWBdzvfn9E=/s.glbimg.com/jo/eg/f/original/2016/11/18/fsdfdsf.jpg',
    'http://s2.glbimg.com/p8eze6X7iY-mNFa5iGUHFQNEhgY=/s.glbimg.com/jo/eg/f/original/2016/11/18/fdsafsad.jpg',
    'https://pbs.twimg.com/media/CxeUjl6WEAAvO0E.jpg',
    'https://pbs.twimg.com/media/CwrpR_fXEAA5uan.jpg',
    'https://pbs.twimg.com/media/Cxf57rfXEAAUHQV.jpg',
    'https://pbs.twimg.com/media/Cxlx2sMW8AA37qh.jpg',
    'https://pbs.twimg.com/media/CxkgKCZXgAAlkO2.jpg',
]

class JoseMemes(jcommon.Extension):
    def __init__(self, cl):
        self.memes = {}
        self.WIDE_MAP = dict((i, i + 0xFEE0) for i in range(0x21, 0x7F))
        self.WIDE_MAP[0x20] = 0x3000
        self.patterns = ['fbcdn.net', 'akamaihd.net']
        jcommon.Extension.__init__(self, cl)

    async def ext_load(self):
        r = await self.load_memes()
        return r

    async def ext_unload(self):
        # supress every kind of debug to self.say
        old_cur = self.current
        self.current = None
        ok = await self.save_memes()
        self.currrent = old_cur
        return ok, ""

    async def load_memes(self):
        try:
            self.memes = pickle.load(open('ext/josememes.db', 'rb'))
            return True, ''
        except Exception as e:
            if self.current is not None:
                await self.debug("load_memes: erro carregando josememes.db(%s)" % e)
                return False, 'error loading josememes.db(%s)' % e
            else:
                self.logger.error("load_memes: %s", e)
                return False, e
            self.memes = {}

    async def save_memes(self):
        try:
            pickle.dump(self.memes, open("ext/josememes.db", 'wb'))
            return True
        except Exception as e:
            self.logger.error("Error in save_memes", exc_info=True)
            return False

    async def c_aprovado(self, message, args, cxt):
        '''`j!aprovado` - O Melhor Sean Anthony®'''
        await cxt.say('http://gaveta.com.br/images/Aprovacao-Sean-Anthony.png')

    async def c_htmpr(self, message, args, cxt):
        await cxt.say(MEMES_TECH_HELP)

    async def do_patterns(self, cxt, meme, url):
        for pat in self.patterns:
            if re.search(pat, url):
                # if facebook, upload to Discord
                await cxt.say("Facebook URL detected, uploading to Discord")

                with aiohttp.ClientSession() as session:
                    data = io.BytesIO()

                    async with session.get(url) as resp:
                        data_read = await resp.read()
                        data.write(data_read)

                    clone = io.BytesIO(data.getvalue())
                    msg = await self.client.send_file(cxt.message.channel, \
                        clone, filename='%s.jpg' % meme, content='*treated*')
                    data.close()
                    clone.close()

                    url = msg.attachments[0]['url']
                    break
        return url

    async def c_meme(self, message, args, cxt):
        '''
        j!meme: Adicione e mostre memes com o josé!
        **RECOMENDADO**: use `!htmpr` para descobrir problemas técnicos.
        *alias*: j!m

        Subcomandos:
        `j!meme add <trigger>;<meme>` - toda vez que alguém mandar um `!meme get <trigger>`, josé falará `<meme>`(limite de <trigger> é 96 chars)
        `j!meme get <trigger>` - josé falará o que estiver programado para falar de acordo com `<trigger>`
        `j!meme search <termo>` - procura o banco de dados de memes por um meme específico
        `j!meme rm <meme>` - remove um meme
        `j!meme rename <nome antigo>;<nome novo>` - altera o `<trigger>` de um meme
        `j!meme owner <meme>` - mostra quem "criou" o `<meme>`
        `j!meme count` - mostra a quantidade de memes
        `j!meme stat` - estatísticas sobre o uso dos memes
        `j!meme istat <meme>` - estatísticas individuais sobre um meme
        `j!meme page <página>` - mostra a página tal de todos os memes disponíveis(inicia de 1, não do 0)
        `j!meme see @user <página>` - mostra todos os memes que a @pessoa fez(`página` inicia de 0, não de 1)
        `j!meme check` - checa o banco de dados de memes
        `j!meme rand` - meme aleatório
        `j!meme searchc <termos>` - procura o DB de meme qual o valor do meme que bate com os termos

        Tenha cuidado ao adicionar coisas NSFW.
        '''

        if len(args) < 2:
            await cxt.say(self.c_meme.__doc__)
            return

        command = args[1]
        if command == 'add':
            args_s = ' '.join(args[2:])
            args_sp = args_s.split(';')
            try:
                meme = args_sp[0]
                url = args_sp[1]
            except IndexError:
                await cxt.say("Error parsing arguments")
                return

            if len(meme) > 96:
                await cxt.say("*não tem meme grátis*")
                return

            if meme in self.memes:
                await cxt.say("%s: meme já existe", (meme,))
                return

            url = await self.do_patterns(cxt, meme, url)

            # create meme in database
            self.memes[meme] = {
                'owner': message.author.id,
                'data': url,
                'uses': 0,
            }

            # save it because of my sanity
            await self.save_memes()
            await cxt.say("%s: meme adicionado!", (meme,))
            return
        elif command == 'rm':
            meme = ' '.join(args[2:])
            if meme in self.memes:
                meme_owner = self.memes[meme]['owner']
                is_admin = await self.b_isowner(cxt)

                if (message.author.id == meme_owner) or is_admin:
                    del self.memes[meme]
                    await self.save_memes()
                    await cxt.say("%s: meme removido", (meme,))
                    return
                else:
                    raise je.PermissionError()

                return
            else:
                await cxt.say("%s: meme não encontrado", (meme,))
                return
        elif command == 'save':
            done = await self.save_memes()
            if done:
                await cxt.say("jmemes: banco de dados salvo")
            else:
                raise IOError("banco de dados não salvo corretamente")

            return

        elif command == 'saveload':
            self.logger.info("saveloading meme database")
            done = await self.save_memes()
            if done:
                await cxt.say("jmemes: banco de dados salvo")
            else:
                raise IOError("banco de dados não salvo corretamente")

            done = await self.load_memes()
            if done:
                await cxt.say("jmemes: banco de dados carregado")
            else:
                raise IOError("banco de dados não carregado corretamente")

            return
        elif command == 'get':
            meme = ' '.join(args[2:])
            if meme in self.memes:
                self.memes[meme]['uses'] += 1
                await cxt.say(self.memes[meme]['data'])
                await self.save_memes()
            else:
                # find other memes that are like the not found one
                probables = [key for key in self.memes if meme in key.lower()]
                if len(probables) > 0:
                    await cxt.say("Didn't you mean `%s`?", (','.join(probables),))
                else:
                    await cxt.say("%s: meme não encontrado", (meme,))
            return
        elif command == 'search':
            term = ' '.join(args[2:])
            term = term.lower()
            if term.strip() == '':
                await cxt.say("Pesquisas vazias não são permitidas")
                return

            # better than google
            probables = [key for key in self.memes if term in key.lower()]
            if len(probables) > 0:
                to_send = ', '.join(probables)
                # check length of message
                if len(to_send) > 1995: # 1 9 9 5
                    await cxt.say(":elephant: Resultados muito grandes :elephant:")
                else:
                    await cxt.say(self.codeblock("", to_send))
            else:
                await cxt.say("%r: Nenhum resultado encontrado", (term,))
        elif command == 'rename':
            args_s = ' '.join(args[2:])
            args_sp = args_s.split(';')
            try:
                oldname = args_sp[0]
                newname = args_sp[1]
            except Exception as e:
                await cxt.say("Error parsing arguments: %r", (e,))

            if oldname not in self.memes:
                await cxt.say("%s: meme não encontrado", (oldname,))
                return

            # swapping
            old_meme = self.memes[oldname]

            if old_meme['owner'] != message.author.id:
                raise je.PermissionError()

            if newname in self.memes:
                await cxt.say("`%s`: meme já existe", (newname,))
                return

            self.memes[newname] = {
                'owner': message.author.id,
                'data': old_meme['data'],
            }

            del self.memes[oldname]
            await cxt.say("`%s` foi renomeado para `%s`!", (oldname, newname))
            await self.save_memes()
            return

        elif command == 'owner':
            meme = ' '.join(args[2:])
            if meme in self.memes:
                u = discord.utils.get(self.client.get_all_members(), \
                    id = self.memes[meme]['owner'])
                await cxt.say("%s foi criado por %s", (meme, u))
            else:
                await cxt.say("%s: meme não encontrado", (meme,))
            return

        elif command == 'count':
            await cxt.say("quantidade de memes: %d", (len(self.memes),))

        elif command == 'stat':
            stat = ''

            copy = dict(self.memes)

            inconsistency = False
            for k in copy:
                inconsistency_report = ''
                if 'uses' not in copy[k]:
                    inconsistency_report += "%s, " % k
                    inconsistency = True

            if inconsistency:
                await cxt.say("INCONSISTENCY: `%s`", (inconsistency_report,))
                return

            i = 1
            for key in sorted(copy, key=lambda key: -copy[key]['uses'])[:10]:
                stat += '%d. %s used %d times\n' % (i, \
                    key, copy[key]['uses'])
                i += 1

            await cxt.say(self.codeblock('', stat))
            return

        elif command == 'istat':
            meme = ' '.join(args[2:])
            if meme in self.memes:
                await cxt.say(self.codeblock('', 'uses: %d'), (self.memes[meme]['uses'],))
            else:
                await cxt.say("%s: meme não encontrado", (meme,))
            return

        elif command == 'page':
            if len(args) < 3:
                await cxt.say("SyntaxError: `!m page <page>`")
                return
            page = args[2]

            try:
                page = int(page)
            except Exception as e:
                await cxt.say("jmemes: %r", (e,))
                return

            if page < 0:
                await cxt.say("EI EI EI EI CALMAI CUZAO")
                return

            PER_PAGE = 50
            min_it = PER_PAGE * (page - 1)
            max_it = PER_PAGE * page

            x = sorted(self.memes.keys())
            x_slice = x[min_it:max_it]

            if len(x_slice) < 1:
                await cxt.say("*nao tem meme gratis*")
                return

            report = ', '.join(x_slice)
            await cxt.say(report)

        elif command == 'check':
            for key in self.memes:
                meme = self.memes[key]
                if 'uses' not in meme:
                    await cxt.say("INCONSISTENCY(uses): %s", (key,))
                    self.memes[key].update({"uses": 0})

            new_memes = {}
            for k in self.memes:
                v = self.memes[k]
                if v['data'] not in new_memes:
                    new_memes[v['data']] = []
                new_memes[v['data']].append(k)

            for v in new_memes:
                if len(new_memes[v]) > 1:
                    await cxt.say("DUPLICATE(s): ```%s```\n", (new_memes[v],))

            await cxt.say("done.")
            return

        elif command == 'see':
            owner = args[2]
            try:
                page = int(args[3])
            except:
                page = 0

            owner_id = await jcommon.parse_id(owner, message)

            from_owner = [x for x in self.memes if self.memes[x]['owner'] == owner_id]
            if len(from_owner) < 1:
                await cxt.say("*nao tem owner gratis*")
                return

            corte = from_owner[page*50:(page+1)*50]
            res = len(from_owner), len(corte), ', '.join(corte)
            report = '''Quantidade: %d[%d],\nMemes: %s''' % (res)
            await cxt.say(report)

        elif command == 'rand':
            key = random.choice(list(self.memes.keys()))
            await cxt.say('%s: %s', (key, self.memes[key]['data'],))

        elif command == 'searchc':
            terms = ' '.join(args[2:])
            terms = terms.lower()
            if terms.strip() == '':
                await cxt.say("Pesquisas vazias não são permitidas")
                return

            probables = [key for key in self.memes if terms in self.memes[key]['data'].lower()]
            if len(probables) <= 70:
                await cxt.say("Results: %s", (', '.join(probables),))
            elif len(probables) > 70:
                await cxt.say("[%d results]", (len(probables),))
            else:
                await cxt.say("%r: No Results", (terms,))

        else:
            await cxt.say("Invalid command: %s", (command,))

        return

    async def c_m(self, message, args, cxt):
        '''`j!m` - alias para `!meme`'''
        await self.c_meme(message, args, cxt)

    async def c_fullwidth(self, message, args, cxt):
        '''`j!fullwidth texto` - converte texto para fullwidth'''
        # looks like discord made fullwidth suppoert available again :D
        text = ' '.join(args[1:])
        if len(text.strip()) <= 0:
            return

        await cxt.say(text.translate(self.WIDE_MAP))

    async def c_fw(self, message, args, cxt):
        '''`j!fw` - alias para `!fullwidth`'''
        await self.c_fullwidth(message, args, cxt)

    async def c_emoji(self, message, args, cxt):
        '''`j!emoji [qt]` - gera de 1 a 5(ou `qt`(máx. 512)) emojis aleatórios'''
        res = ''
        if len(args) < 2:
            res = await jcommon.random_emoji(random.randint(1,5))
        else:
            a = int(args[1])
            if a < 1:
                await cxt.say("*Emojis inexistentes*")
                return
            if a >= 512:
                await cxt.say("*Não tem emoji grátis*")
                return
            res = await jcommon.random_emoji(int(args[1]))
        await cxt.say(res)

    async def c_blackmirror(self, message, args, cxt):
        '''`j!blackmirror` - COISAS MUITO BLACK MIRROR, MEU'''
        mensagem_muito_blackmirror = random.choice(BLACK_MIRROR_MESSAGES)
        await cxt.say(mensagem_muito_blackmirror)

    async def wikimedia_api(self, params, cxt):
        using_query = False
        wiki_searchterm = ' '.join(params['args'][1:])

        if len(wiki_searchterm.strip()) < 1:
            await cxt.say("Empty search query")
            return

        wiki_methodname = params['name']

        wiki_api_endpoint = params['endpoint']
        wiki_api_params = params['searchparams']
        if 'queryparams' in params:
            wiki_api_params = params['queryparams']
            using_query = True

        wiki_api_url = '%s%s%s' % (wiki_api_endpoint, wiki_api_params,
            urllib.parse.quote(wiki_searchterm))

        self.logger.info("Wiki request: %s", wiki_api_url)
        try:
            response = await asyncio.wait_for(aiohttp.request('GET', wiki_api_url), 4)
        except asyncio.TimeoutError:
            await cxt.say("`[wiki:%s] Timeout reached`", (wiki_methodname,))
            return

        response_text = await response.text()
        wiki_json = json.loads(response_text)

        if using_query:
            self.logger.debug("Wiki: Use query method")
            w_search_data = wiki_json['query']['search']
            w_all = ''
            for result in w_search_data[:6]:
                w_snippet = result['snippet']
                w_snippet = w_snippet.replace('<span class=\"searchmatch\">', '')
                w_snippet = w_snippet.replace('</span>', '')
                w_all += '\t%s: %s...\n' % (result['title'], w_snippet[:120])
            await cxt.say(self.codeblock(w_all, ''))
            return
        else:
            w_suggestions = wiki_json[1]
            w_suggestions_text = wiki_json[2]
            w_wiki_urls = wiki_json[3]

            if len(w_suggestions) < 1:
                await cxt.say("sem resultados")
                return

            self.logger.debug(w_suggestions_text)
            search_paragaph = w_suggestions_text[0]

            if len(w_suggestions) > 1:
                search_paragaph = 'Múltiplos resultados: %s' % ', '.join(w_suggestions)

            if len(search_paragaph) >= 500:
                search_paragaph = search_paragaph[:500] + '...'

            await cxt.say(
            """`%s:%s` =
```
    %s
    [ URL0: %s ]
```
            """ % (wiki_methodname, wiki_searchterm, search_paragaph, w_wiki_urls[0]))
            return

    async def c_wiki(self, message, args, cxt):
        '''`j!wiki [terms]` - procurar na WIKIPEDIA!!!'''
        wikipedia_params = {
            'name': 'en.wikipedia',
            'args': args,
            'endpoint': 'https://en.wikipedia.org/w/api.php',
            'searchparams': '?format=json&action=opensearch&search=',
            'queryparams': '?format=json&action=query&list=search&utf8=&srsearch='
        }

        if ':query' in args:
            args[args.index(':query')] = ''
            wikipedia_params['searchparams'] = ''
            await self.wikimedia_api(wikipedia_params, cxt)
        else:
            del wikipedia_params['queryparams']
            await self.wikimedia_api(wikipedia_params, cxt)

    async def c_deswiki(self, message, args, cxt):
        '''`j!deswiki [terms]` - procurar na DESCICLOPEDIA!!!'''
        await self.wikimedia_api(
            {
                'name': 'desciclopedia',
                'args': args,
                'endpoint': 'http://desciclopedia.org/api.php',
                'searchparams': '?format=json&action=opensearch&search=',
                #'queryparams': '?format=json&action=query&list=search&srsearch='
            }, cxt
        )

    async def c_ri(self, message, args, cxt):
        inputstr = ' '.join(args[1:]).lower()
        inputstr = list(inputstr)

        for (index, char) in enumerate(inputstr):
            if char.isalpha():
                inputstr[index] = ':regional_indicator_%s:' % char
            elif char in RI_TABLE:
                inputstr[index] = RI_TABLE[char]

        res = ''.join(inputstr)
        await cxt.say(res)

    async def c_pupper(self, message, args, cxt):
        await cxt.say("http://i.imgur.com/9Le8rW7.jpg :sob:")

    async def c_8ball(self, message, args, cxt):
        '''`j!8ball` - 8ball'''
        try:
            response = await asyncio.wait_for(aiohttp.request('GET', \
                'https://api.rtainc.co/twitch/8ball?format=[0]'), 4)
        except asyncio.TimeoutError:
            await cxt.say("`[8ball] Timeout reached`")
            return

        answer = await response.text()
        await cxt.say("**%s**, :8ball: said %s", (str(message.author.name), \
            answer))
