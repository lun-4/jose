#!/usr/bin/env python3

import sys
sys.path.append("..")
import josecommon as jcommon
import jcoin.josecoin as jcoin

import aiohttp
import json
import urllib.parse
import traceback

from random import SystemRandom
random = SystemRandom()

# from xml.etree import ElementTree

PORN_LIMIT = 14

class JoseImages(jcommon.Extension):
    def __init__(self, cl):
        jcommon.Extension.__init__(self, cl)

    async def ext_load(self):
        return True, ''

    async def get_json(self, url):
        r = await aiohttp.request('GET', url)
        r = await r.text()
        r = json.loads(r)
        return r

    async def json_api(self, cxt, index_url, show_url, search_term, post_key, rspec=False, hypnohub_flag=False):
        url = ''
        random_flag = False
        if search_term == ':latest':
            await cxt.say('`[nsfw.json] procurando nos posts mais recentes`')
            url = '%s?limit=%s' % (index_url, PORN_LIMIT)
        elif search_term == ':random':
            await cxt.say('`[nsfw.json] procurando um ID aleatório`')
            random_flag = True
            url = '%s?limit=%s' % (index_url, 1)
        else:
            await cxt.say('`[nsfw.json] procurando por %r`' % search_term)
            url = '%s?limit=%s&tags=%s' % (index_url, PORN_LIMIT, search_term)

        r = await self.get_json(url)

        post = None
        if rspec:
            post = random.choice(r[rspec])
        elif random_flag:
            most_recent_id = r[0]['id']
            random_id = random.randint(1, most_recent_id)
            if not show_url:
                await cxt.say("`[nsfw.json] API não suporta posts individuais`")
                return
            random_post_url = '%s?id=%s' % (show_url, random_id)
            post = await self.get_json(random_post_url)
        else:
            if len(r) < 1:
                await cxt.say("`[nsfw.json] Nenhum resultado encontrado.`")
                return
            post = random.choice(r)

        post_url = post[post_key]
        if hypnohub_flag:
            post_url = post_url.replace('//', '/')
            post_url = 'http:/%s' % post_url
        await cxt.say('ID: %d, URL: %s' % (post['id'], post_url))
        return

    async def porn_routine(self, cxt):
        res = await jcoin.jcoin_control(self.current.author.id, jcommon.PORN_PRICE)
        if not res[0]:
            await cxt.say("PermError: %s" % res[1])
            return False
        return True

    async def c_hypno(self, message, args, cxt):
        access = await self.porn_routine(cxt)
        if access:
            # ¯\_(ツ)_/¯
            await self.json_api(cxt, 'http://hypnohub.net/post/index.json', '',
                ' '.join(args[1:]), 'file_url', None, True)

    async def c_yandere(self, message, args, cxt):
        access = await self.porn_routine(cxt)
        if access:
            await self.json_api(cxt, 'https://yande.re/post.json', '',
                ' '.join(args[1:]), 'file_url')

    async def c_e621(self, message, args, cxt):
        access = await self.porn_routine(cxt)
        if access:
            await self.json_api(cxt, 'https://e621.net/post/index.json', 'https://e621.net/post/show.json',
                ' '.join(args[1:]), 'file_url')

    async def c_porn(self, message, args, cxt):
        access = await self.porn_routine()
        if access:
            await self.json_api(cxt, 'http://api.porn.com/videos/find.json', '',
                ' '.join(args[1:]), 'url', 'result')

    async def c_urban(self, message, args, cxt):
        term = ' '.join(args[1:])

        url = 'http://api.urbandictionary.com/v0/define?term=%s' % urllib.parse.quote(term)
        resp = await aiohttp.request('GET', url)
        content = await resp.text()
        r = json.loads(content)

        try:
            if len(r['list']) < 1:
                await cxt.say("*não tem definição grátis*")
                return
            await cxt.say(self.codeblock('', '%s:\n%s' % (term, r['list'][0]['definition'])))
        except Exception as e:
            await self.debug('```%s```'%traceback.format_exc())
        return
