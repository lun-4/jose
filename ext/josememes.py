#!/usr/bin/env python3

import re
import io
import aiohttp
import string
import asyncio
import sys
from random import SystemRandom
random = SystemRandom()
import pickle

import discord

sys.path.append("..")
import josecommon as jcommon
import jauxiliar as jaux
import joseerror as je
import randemoji as emoji

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

# implement letters
RI_STR = '🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇶🇷🇸🇹🇺🇻🇼🇽🇾🇿'

RI_TABLE.update({letter:RI_STR[string.ascii_lowercase.find(letter)] for \
    letter in string.ascii_lowercase})

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

MAX_MEME_NAME = 96

async def random_emoji(maxn):
    return ''.join((str(emoji.random_emoji()) for i in range(maxn)))

def make_meme_entry(author_id, url, uses=0):
    return {
        'owner': str(author_id),
        'data': url,
        'uses': 0,
    }

class JoseMemes(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)
        self.memes = {}
        self.WIDE_MAP = jcommon.WIDE_MAP
        self.patterns = ['fbcdn.net', 'akamaihd.net']

        self.cbk_new('save_memes', self.save_sentinel, 120)

    async def ext_load(self):
        r = await self.load_memes()
        return r

    async def ext_unload(self):
        ok = await self.save_memes()
        return ok, ""

    async def load_memes(self):
        try:
            self.memes = pickle.load(open('ext/josememes.db', 'rb'))
            return True, ''
        except Exception as e:
            self.logger.error("load_memes: %s", e)
            return False, 'error loading josememes.db(%s)' % e

    async def save_sentinel(self):
        await self.save_memes()

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

    def meme_exists(self, meme_key):
        if meme_key in self.memes:
            return True
        else:
            raise je.CommonError("%s: meme not found" % (meme_key))

    async def c_meme(self, message, args, cxt):
        '''`j!meme add <meme>;<meme_content>` - `j!meme get <meme>`, jose says `<meme_content>`
        `j!meme get <meme>` - get a `<meme>`
        `j!meme search <terms>` - search for specific terms
        `j!meme rm <meme>` - remove meme
        `j!meme rename <old meme key>;<new meme key>` - remove meme name
        `j!meme owner <meme>` - who's the father of the meme
        `j!meme count` - amount of stuff
        `j!meme stat` - statistics
        `j!meme istat <meme>` - individual stats about a meme
        `j!meme page <page>` - all memes(`<page>` starts from 1)
        `j!meme see @user <page>` - shows all memes that @user made(`<page>` starts from 0)
        `j!meme check` - checks meme database for inconsistencies
        `j!meme rand` - random meme
        `j!meme searchc <terms>` - search in the database every meme that its `<meme_content>` contains `<terms>`

        **No NSFW.**
        '''

        if len(args) < 2:
            await cxt.say(self.c_meme.__doc__)
            return

        command = args[1]
        args_s = ' '.join(args[2:])

        if command == 'add':
            args_sp = args_s.split(';')
            try:
                meme = args_sp[0]
                url = args_sp[1]
            except:
                await cxt.say("Error parsing arguments")
                return

            if len(meme) > MAX_MEME_NAME:
                await cxt.say("*meme name is too long*")
                return

            if meme in self.memes:
                await cxt.say("%s: meme already exists", (meme,))
                return

            url = await self.do_patterns(cxt, meme, url)

            # create meme in database
            self.memes[meme] = make_meme_entry(message.author.id, url)

            await cxt.say("%s: meme adicionado!", (meme,))
            return
        elif command == 'rm':
            meme = ' '.join(args[2:])
            self.meme_exists(meme)

            meme_owner = self.memes[meme]['owner']
            is_admin = await self.b_isowner(cxt)


            if (message.author.id != meme_owner) or not is_admin:
                raise je.PermissionError()

            del self.memes[meme]
            await self.save_memes()
            await cxt.say("%s: meme removido", (meme,))
        elif command == 'save':
            done = await self.save_memes()
            if done:
                await cxt.say("jmemes: banco de dados salvo")
            else:
                raise IOError("banco de dados não salvo corretamente")

            return

        elif command == 'saveload':
            self.logger.info("saveloading memedb")

            done = await self.save_memes()
            if not done:
                raise IOError("banco de dados não salvo corretamente")

            done = await self.load_memes()
            if not done:
                raise IOError("banco de dados não carregado corretamente")

            await cxt.say("done")

        elif command == 'get':
            meme = ' '.join(args[2:])
            if meme in self.memes:
                self.memes[meme]['uses'] += 1
                await cxt.say(self.memes[meme]['data'])
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
                await cxt.say("Empty searches? lol")
                return

            # better than google
            probables = [key for key in self.memes if term in key.lower()]
            if len(probables) > 0:
                to_send = ', '.join(probables)
                await cxt.say(self.codeblock("", to_send))
            else:
                await cxt.say("%r: Nenhum resultado encontrado", (term,))

            return
        elif command == 'rename':
            args_sp = args_s.split(';')
            try:
                oldname = args_sp[0]
                newname = args_sp[1]
            except:
                await cxt.say("Error parsing arguments")
                return

            self.meme_exists(oldname)
            old_meme = self.memes[oldname]

            if old_meme['owner'] != message.author.id:
                raise je.PermissionError()

            if newname in self.memes:
                await cxt.say("`%s`: meme já existe", (newname,))
                return

            # swapping
            self.memes[newname] = make_meme_entry(message.author.id, \
                old_meme['data'], old_meme['uses'])
            del self.memes[oldname]

            await cxt.say("`%s` is now `%s`!", (oldname, newname))

        elif command == 'owner':
            meme = ' '.join(args[2:])
            self.meme_exists(meme)

            u = discord.utils.get(self.client.get_all_members(), \
                id = self.memes[meme]['owner'])
            await cxt.say("%s foi criado por %s", (meme, u))

        elif command == 'count':
            await cxt.say("quantidade de memes: %d", (len(self.memes),))

        elif command == 'stat':
            stat = []
            ordered = sorted(self.memes, key=lambda key: self.memes[key]['uses'], reverse=True)
            for (i, key) in enumerate(ordered[:15]):

                stat.append('[%2d] %s used %d times' % \
                    (i, key, self.memes[key]['uses']))
                i += 1

            await cxt.say(self.codeblock('', '\n'.join(stat)))

        elif command == 'istat':
            meme = ' '.join(args[2:])
            self.meme_exists(meme)
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

            page_slice = from_owner[page * 50:(page + 1) * 50]
            res = len(from_owner), len(page_slice), ', '.join(page_slice)
            report = '''Showing %d[%d in page],\nMemes: %s''' % (res)
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
        '''`j!fullwidth text` - converts text to full width'''
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
            res = await random_emoji(random.randint(1, 5))
        else:
            a = int(args[1])
            if a < 1:
                await cxt.say("*Emojis inexistentes*")
                return
            if a >= 512:
                await cxt.say("*Não tem emoji grátis*")
                return
            res = await random_emoji(int(args[1]))
        await cxt.say(res)

    async def c_blackmirror(self, message, args, cxt):
        '''`j!blackmirror` - COISAS MUITO BLACK MIRROR, MEU'''
        mensagem_muito_blackmirror = random.choice(BLACK_MIRROR_MESSAGES)
        await cxt.say(mensagem_muito_blackmirror)

    async def c_ri(self, message, args, cxt):
        inputstr = ' '.join(args[1:]).lower()
        if len(inputstr) < 1:
            await cxt.say("Can't make R.I. out from nothing")
            return

        inputstr = list(inputstr)

        for (index, char) in enumerate(inputstr):
            if char in RI_TABLE:
                inputstr[index] = '{} '.format(RI_TABLE[char])

        res = ''.join(inputstr)
        await cxt.say(res)

    async def c_pupper(self, message, args, cxt):
        await cxt.say("http://i.imgur.com/9Le8rW7.jpg :sob:")

    async def c_8ball(self, message, args, cxt):
        '''`j!8ball` - 8ball'''
        await self.jcoin_pricing(cxt, jcommon.API_TAX_PRICE)

        try:
            answer = await self.http_get('https://api.rtainc.co/twitch/8ball?format=[0]', timeout=4)
        except asyncio.TimeoutError:
            await cxt.say("`[8ball] Timeout reached`")
            return

        await cxt.say("**%s**, :8ball: said %s", (str(message.author.name), \
            answer))
