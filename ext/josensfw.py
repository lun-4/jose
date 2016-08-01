#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import josecommon as jcommon

import os
import time
import aiohttp
import json

from random import SystemRandom
random = SystemRandom()

from xml.etree import ElementTree
import jcoin.josecoin as jcoin

PORN_LIMIT = 14

class JoseNSFW(jcommon.Extension):
    def __init__(self, cl):
        jcommon.Extension.__init__(self, cl)

    @asyncio.coroutine
    def danbooru_api(self, baseurl, search_term):
        loop = asyncio.get_event_loop()

        url = ''
        if search_term == ':latest':
            yield from self.say('danbooru: procurando nos posts mais recentes')
            url = '%s?limit=%s' % (baseurl, PORN_LIMIT)
        else:
            yield from self.say('dbru_api: procurando por %r' % search_term)
            url = '%s?limit=%s&tags=%s' % (baseurl, PORN_LIMIT, search_term)

        r = yield from aiohttp.request('GET', url)
        content = yield from r.text()

        tree = ElementTree.fromstring(content)
        root = tree

        try:
            post = random.choice(root)
            yield from self.say('%s' % post.attrib['file_url'])
            return
        except Exception as e:
            yield from self.debug("danbooru: py_error: %s" % str(e))
            return

    @asyncio.coroutine
    def json_api(self, baseurl, search_term, where):
        loop = asyncio.get_event_loop()

        url = ''
        if search_term == ':latest':
            yield from self.say('json_api: procurando nos posts mais recentes')
            url = '%s?limit=%s' % (baseurl, PORN_LIMIT)
        else:
            yield from self.say('json_api: procurando por %r' % search_term)
            url = '%s?limit=%s&tags=%s' % (baseurl, PORN_LIMIT, search_term)

        r = yield from aiohttp.request('GET', url)
        r = yield from r.text()
        r = json.loads(r)

        try:
            post = random.choice(r)
            yield from self.say('%s' % post[where])
            return
        except Exception as e:
            yield from self.debug("json_api: py_error: %s" % str(e))
            return

    @asyncio.coroutine
    def porn_routine(self):
        res = yield from jcoin.jcoin_control(self.current.author.id, jcommon.PORN_PRICE)
        if not res[0]:
            yield from client.send_message(message.channel,
                "PermError: %s" % res[1])
            return False
        return True

    @asyncio.coroutine
    def c_hypno(self, message, args):
        access = yield from self.porn_routine()
        if access:
            # ¯\_(ツ)_/¯
            yield from self.danbooru_api('http://hypnohub.net/post/index.xml', ' '.join(args[1:]))

    @asyncio.coroutine
    def c_yandere(self, message, args):
        access = yield from self.porn_routine()
        if access:
            yield from self.danbooru_api('https://yande.re/post.xml', ' '.join(args[1:]))

    @asyncio.coroutine
    def c_e621(self, message, args):
        access = yield from self.porn_routine()
        if access:
            yield from self.json_api('https://e621.net/post/index.json', ' '.join(args[1:]), 'file_url')

    @asyncio.coroutine
    def c_porn(self, message, args):
        access = yield from self.porn_routine()
        if access:
            yield from self.json_api('http://api.porn.com/videos/find.json', ' '.join(args[1:]), 'url')
