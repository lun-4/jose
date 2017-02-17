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

IMAGE_LIMIT = 14

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

    async def json_api(self, cxt, config):
        '''
        {
            'search_term': stuff to search,
            'index_url': where are the latest posts,
            'search_url': search for stuff(defaults to index_url),
            'show_url': get individual posts,
            'post_key': where to get the post image URL,
            'limit_key': what is the tag to limit results,
            'search_key': what is the tag to search in search_url,
        }
        '''
        search_term = config.get('search_term')
        index_url = config.get('index_url')
        search_url = config.get('search_url', index_url)
        show_url = config.get('show_url')
        post_key = config.get('post_key')
        rspec = config.get('rspec')
        limit_key = config.get('limit_key', 'limit')
        search_key = config.get('search_key', 'tags')
        random_flag = False

        if search_term == '-latest':
            # get latest
            await cxt.say('`[img.json] most recent posts`')
            url = '%s?limit=%s' % (index_url, IMAGE_LIMIT)
        elif search_term == '-random':
            # random id
            await cxt.say('`[img.json] random ID`')
            random_flag = True
            url = '%s?limit=%s' % (index_url, 1)
        else:
            # normally, search tags
            await cxt.say('`[img.json] tags: %r`' % search_term)
            url = '%s?%s=%s&%s=%s' % (search_url, limit_key, IMAGE_LIMIT,\
                search_key, search_term)

        response = await self.get_json(url)

        post = None
        if rspec:
            post = random.choice(response[rspec])
        elif random_flag:
            most_recent_id = response[0]['id']
            random_id = random.randint(1, most_recent_id)
            if not show_url:
                await cxt.say("`[img.json] API doesn't support individual posts`")
                return
            random_post_url = '%s?id=%s' % (show_url, random_id)
            post = await self.get_json(random_post_url)
        else:
            if len(response) < 1:
                await cxt.say("`[img.json] No results found.`")
                return
            post = random.choice(response)

        post_url = post[post_key]
        if 'hypnohub' in post_url:
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
            await self.json_api(cxt, {
                'search_term': ' '.join(args[1:]),
                'index_url': 'http://hypnohub.net/post/index.json',
                'post_key': 'image',
            })

    async def c_yandere(self, message, args, cxt):
        access = await self.porn_routine(cxt)
        if access:
            await self.json_api(cxt, {
                'search_term': ' '.join(args[1:]),
                'index_url': 'https://yande.re/post.json',
                'post_key': 'file_url',
            })

    async def c_e621(self, message, args, cxt):
        access = await self.porn_routine(cxt)
        if access:
            await self.json_api(cxt, {
                'search_term': ' '.join(args[1:]),
                'index_url': 'https://e621.net/post/index.json',
                'show_url': 'https://e621.net/post/show.json',
                'post_key': 'file_url',
            })

    async def c_derpibooru(self, message, args, cxt):
        access = await self.porn_routine()
        if access:
            await self.json_api(cxt, {
                'search_term': ' '.join(args[1:]),
                'search_url': 'derpibooru.org/search.json',
                'index_url': 'derpibooru.org/images.json',
                'show_url': 'derpibooru.org/%d.json',
                'post_key': 'image',
                'limit_key': 'page',
                'search_key': 'q',
            })

    async def c_urban(self, message, args, cxt):
        term = ' '.join(args[1:])

        url = 'http://api.urbandictionary.com/v0/define?term=%s' % urllib.parse.quote(term)
        resp = await aiohttp.request('GET', url)
        content = await resp.text()
        r = json.loads(content)

        try:
            if len(r['list']) < 1:
                await cxt.say("*no free definitions*")
                return
            await cxt.say(self.codeblock('', '%s:\n%s' % (term, r['list'][0]['definition'])))
        except Exception as e:
            await self.debug('```%s```'%traceback.format_exc())
        return
