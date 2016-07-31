#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import josecommon as jcommon

import os
import time
import requests
from xml.etree import ElementTree

class JoseNSFW(jcommon.Extension):
    def __init__(self, cl):
        jcommon.Extension.__init__(self, cl)

    @asyncio.coroutine
    def danbooru_api(self, baseurl, search_term):
        loop = asyncio.get_event_loop()

        url = ''
        if search_term == ':latest':
            yield from self.say('dbru_api: procurando nos posts mais recentes')
            url = '%s?limit=%s' % (baseurl, PORN_LIMIT)
        else:
            yield from self.say('dbru_api: procurando por %r' % search_term)
            url = '%s?limit=%s&tags=%s' % (baseurl, PORN_LIMIT, search_term)

        future_stmt = loop.run_in_executor(None, requests.get, url)
        r = yield from future_stmt

        tree = ElementTree.fromstring(r.content)
        root = tree

        try:
            post = random.choice(root)
            yield from self.say('%s' % post.attrib['file_url'])
            return
        except Exception as e:
            yield from self.debug("dbru_api: py_error: %s" % str(e))
            return

    @asyncio.coroutine
    def json_api(self, post_endpoint, search_terms):
        pass

    @asyncio.coroutine
    def porn_routine(self):
        res = yield from jcoin_control(message.author.id, PORN_PRICE)
        if not res[0]:
            yield from client.send_message(message.channel,
                "PermError: %s" % res[1])
            return False
        return True

    @asyncio.coroutine
    def c_hypno(self, message, args):
        pass

    @asyncio.coroutine
    def c_e621(self, message, args):
        pass

    @asyncio.coroutine
    def c_yandere(self, message, args):
        pass

    @asyncio.coroutine
    def c_porn(self, message, args):
        pass
