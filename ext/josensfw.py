#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import josecommon as jcommon
import jcoin.josecoin as jcoin
import joseerror as je

import os
import time
import aiohttp
import json
import urllib.parse
import traceback

from random import SystemRandom
random = SystemRandom()

from xml.etree import ElementTree

PORN_LIMIT = 14

class JoseNSFW(jcommon.Extension):
    def __init__(self, cl):
        jcommon.Extension.__init__(self, cl)

    async def danbooru_api(self, baseurl, search_term):
        loop = asyncio.get_event_loop()

        url = ''
        if search_term == ':latest':
            await self.say('danbooru: procurando nos posts mais recentes')
            url = '%s?limit=%s' % (baseurl, PORN_LIMIT)
        else:
            await self.say('dbru_api: procurando por %r' % search_term)
            url = '%s?limit=%s&tags=%s' % (baseurl, PORN_LIMIT, search_term)

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
            return

    async def json_api(self, baseurl, search_term, where):
        loop = asyncio.get_event_loop()

        url = ''
        if search_term == ':latest':
            await self.say('json_api: procurando nos posts mais recentes')
            url = '%s?limit=%s' % (baseurl, PORN_LIMIT)
        else:
            await self.say('json_api: procurando por %r' % search_term)
            url = '%s?limit=%s&tags=%s' % (baseurl, PORN_LIMIT, search_term)

        r = await aiohttp.request('GET', url)
        r = await r.text()
        r = json.loads(r)

        try:
            post = random.choice(r)
            await self.say('%s' % post[where])
            return
        except Exception as e:
            await self.debug("json_api: py_error: %s" % str(e))
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
            await self.danbooru_api('http://hypnohub.net/post/index.xml', ' '.join(args[1:]))

    async def c_yandere(self, message, args):
        access = await self.porn_routine()
        if access:
            await self.danbooru_api('https://yande.re/post.xml', ' '.join(args[1:]))

    async def c_e621(self, message, args):
        access = await self.porn_routine()
        if access:
            await self.json_api('https://e621.net/post/index.json', ' '.join(args[1:]), 'file_url')

    async def c_porn(self, message, args):
        access = await self.porn_routine()
        if access:
            await self.json_api('http://api.porn.com/videos/find.json', ' '.join(args[1:]), 'url')

    async def c_urban(self, message, args):
        term = ' '.join(args[1:])

        url = 'http://api.urbandictionary.com/v0/define?term=%s' % urllib.parse.quote(term)
        resp = await aiohttp.request('GET', url)
        content = await resp.text()
        r = json.loads(content)

        try:
            await self.say(self.codeblock('', '%s:\n%s' % (term, r['list'][0]['definition'])))
        except Exception as e:
            await self.debug('```%s```'%traceback.format_exc())
        return
