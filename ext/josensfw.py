#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import josecommon as jcommon
import jcoin.josecoin as jcoin
import joseerror as je

import aiohttp
import json
import urllib.parse
import traceback

from random import SystemRandom
random = SystemRandom()

# from xml.etree import ElementTree

PORN_LIMIT = 14

class JoseNSFW(jcommon.Extension):
    def __init__(self, cl):
        jcommon.Extension.__init__(self, cl)

    '''async def danbooru_api(self, index_url, search_term):
        url = ''
        if search_term == ':latest':
            await self.say('dbru_api: procurando nos posts mais recentes')
            url = '%s?limit=%s' % (index_url, PORN_LIMIT)
        elif search_term == ':random':
            await self.say('json_api: procurando um ID aleatório')
            random_flag = True
            url = '%s?limit=%s' % (index_url, 1)
        else:
            await self.say('dbru_api: procurando por %r' % search_term)
            url = '%s?limit=%s&tags=%s' % (index_url, PORN_LIMIT, search_term)

        r = await aiohttp.request('GET', url)
        content = await r.text()

        tree = ElementTree.fromstring(content)
        root = tree

        try:
            post = random.choice(root)
            await self.say('%s' % post.attrib['file_url'])
            return
        except Exception as e:
            await self.debug("danbooru: py_error: %s" % str(e))
            return'''

    async def get_json(self, url):
        r = await aiohttp.request('GET', url)
        r = await r.text()
        r = json.loads(r)
        return r

    async def json_api(self, index_url, show_url, search_term, post_key, rspec=False, hypnohub_flag=False):
        url = ''
        random_flag = False
        if search_term == ':latest':
            await self.say('json_api: procurando nos posts mais recentes')
            url = '%s?limit=%s' % (index_url, PORN_LIMIT)
        elif search_term == ':random':
            await self.say('json_api: procurando um ID aleatório')
            random_flag = True
            url = '%s?limit=%s' % (index_url, 1)
        else:
            await self.say('json_api: procurando por `%r`' % search_term)
            url = '%s?limit=%s&tags=%s' % (index_url, PORN_LIMIT, search_term)

        r = await self.get_json(url)

        try:
            post = None
            if rspec:
                post = random.choice(r[rspec])
            elif random_flag:
                most_recent_id = r[0]['id']
                random_id = random.randint(1, most_recent_id)
                if not show_url:
                    await self.say("json_api: API não suporta posts individuais")
                    return

                random_post_url = '%s?id=%s' % (show_url, random_id)
                post = await self.get_json(random_post_url)
            else:
                post = random.choice(r)

            post_url = post[post_key]
            if hypnohub_flag:
                post_url = post_url.replace('//', '/')
                post_url = 'http:/%s' % post_url
            await self.say('ID: %d, URL: %s' % (post['id'], post_url))
            return
        except Exception as e:
            await self.debug("json_api: py_error: %r" % e)
            return

    async def porn_routine(self):
        res = await jcoin.jcoin_control(self.current.author.id, jcommon.PORN_PRICE)
        if not res[0]:
            await client.send_message(message.channel,
                "PermError: %s" % res[1])
            return False
        return True

    async def c_hypno(self, message, args):
        access = await self.porn_routine()
        if access:
            # ¯\_(ツ)_/¯
            await self.json_api('http://hypnohub.net/post/index.json', '',
                ' '.join(args[1:]), 'file_url', None, True)

    async def c_yandere(self, message, args):
        access = await self.porn_routine()
        if access:
            await self.json_api('https://yande.re/post.json', '',
                ' '.join(args[1:]), 'file_url')

    async def c_e621(self, message, args):
        access = await self.porn_routine()
        if access:
            await self.json_api('https://e621.net/post/index.json', 'https://e621.net/post/show.json',
                ' '.join(args[1:]), 'file_url')

    async def c_porn(self, message, args):
        access = await self.porn_routine()
        if access:
            await self.json_api('http://api.porn.com/videos/find.json', '',
                ' '.join(args[1:]), 'url', 'result')

    async def c_urban(self, message, args):
        term = ' '.join(args[1:])

        url = 'http://api.urbandictionary.com/v0/define?term=%s' % urllib.parse.quote(term)
        resp = await aiohttp.request('GET', url)
        content = await resp.text()
        r = json.loads(content)

        try:
            if len(r['list']) < 1:
                await self.say("*não tem definição grátis*")
                return
            await self.say(self.codeblock('', '%s:\n%s' % (term, r['list'][0]['definition'])))
        except Exception as e:
            await self.debug('```%s```'%traceback.format_exc())
        return
