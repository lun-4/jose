#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import josecommon as jcommon

import os
import time
import requests

class JoseNSFW(jcommon.Extension):
    def __init__(self, cl):
        jcommon.Extension.__init__(self, cl)

    @asyncio.coroutine
    def danbooru_api(self, post_endpoint, search_terms):
        pass

    @asyncio.coroutine
    def json_api(self, post_endpoint, search_terms):
        pass

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
