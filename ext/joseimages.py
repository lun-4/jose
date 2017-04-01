#!/usr/bin/env python3

import sys
sys.path.append("..")
import josecommon as jcommon
import jauxiliar as jaux
import joseerror as je

import aiohttp
import json
import urllib.parse
import traceback
import logging

from random import SystemRandom
random = SystemRandom()

IMAGE_LIMIT = 14

PUDDING_MOE = 'http://pudding.moe'

async def test_generator():
    img_number = 1
    img_extension = '.png'
    if random.randint(0, 26) == 1:
        img_number += random.randint(0, 38)
        img_extension = '.gif'
    else:
        img_number += random.randint(0, 519)

    return "{}/homepage/random/{}.{}".format(PUDDING_MOE, img_number, img_extension)


HYPNOHUB_CONFIG = {
    'name': 'hypnohub',
    'urls': {
        'index': 'https://hypnohub.net/post/index.json',
        'show': 'https://hypnohub.net/post/index.json',
    },
    'keys': {
        'post': 'file_url',
        'id': 'id:',
    },
    'id_tags': True,
}

YANDERE_CONFIG = {
    'name': 'yandere',
    'urls': {
        'index': 'https://yande.re/post.json',
    },
    'keys': {
        'post': 'file_url',
    },
}

E621_CONFIG = {
    'name': 'e621',
    'urls': {
        'index': 'https://e621.net/post/index.json',
        'show': 'https://e621.net/post/show.json',
    },
    'keys': {
        'post': 'file_url',
    }
}

DERPIBOORU_CONFIG = {
    'name': 'derpibooru',
    'urls': {
        'index': 'http://derpibooru.org/images.json',
        'search': 'http://derpibooru.org/search.json',
    },
    'keys': {
        'post': 'image',
        'limit': 'page',
        'search': 'q',
        'posts': 'images',
        'from_search': 'search',
    }
}

logger = logging.getLogger('images')

def img_function(board_config):
    _cfg = board_config.get

    board_id = _cfg('name')
    _key = _cfg('keys', {}).get
    _url = _cfg('urls', {}).get

    id_tags         _cfg('id_tags', False)

    '''
        index_url: index page of the image board
        search_url: get one post based on the tags (default index_url)
        show_url: get one post based on its ID
    '''

    index_url =     _url('index')
    search_url =    _url('search', index_url)
    show_url =      _url('show')

    '''
        post_key: where to get the post's URL
        id_key: where to get the post's ID
        limit_key: the key to limit posts returned by the API
        search_key: the key in the URL to send tags to
        posts_key: the key where the API gives its posts data
    '''

    post_key =          _key('post', 'file_url')
    id_key =            _key('id', 'id=')
    limit_key =         _key('limit', 'limit')
    search_key =        _key('tags', 'tags')
    posts_key =         _key('posts', False)
    from_search_key =   _key('from_search')

    async def func(json_function, cxt, search_data):
        nonlocal post_key, id_key, limit_key, posts_key, from_search_key

        random_flag = False
        post, url = None, ''
        lmt_params = f'{limit_key}={IMAGE_LIMIT}'
        srch_params = f'{search_key}={search_data}'

        if search_data == '-latest':
            url = f'{index_url}?{lmt_params}'
        elif search_data == '-random':
            random_flag = True
            url = f'{index_url}?{limit_key}=1'
        else:
            url = f'{search_url}?{lmt_params}&{srch_params}'
            if from_search_key:
                posts_key = from_search_key
        try:
            response = await json_function(url)
        except je.JSONError as err:
            await cxt.say("`[%s] JSONError@%r: %r`", (board_id, url, err))
            return

        logger.info('[%s] %r %r', board_id, posts_key, search_data)

        if posts_key:
            response = response[posts_key]

        if len(response) < 1:
            await cxt.say("`[%s] No results found.`", (board_id,))
            return

        if random_flag and not show_url:
            await cxt.say("`%s` doesn't support individual posts.", (board_id,))
            return

        if random_flag:
            most_recent_id = response[0][id_key]

            # Assume posts start counting from 1
            random_id = random.randint(1, int(most_recent_id))
            rand_post_url = f'{show_url}?{id_key}{random_id}'
            if id_tags:
                rand_post_url = f'{show_url}?{search_key}={id_key}{random_id}'
            post = await json_function(rand_post_url)
        else:
            post = random.choice(response)

        post_url = post[post_key]
        if not post_url.startswith('http'):
            post_url = post_url.replace('//', '/')
            post_url = 'http:/%s' % post_url

        post_id = str(post['id'])
        await cxt.say('ID: %s, URL: %s', (post_id, post_url))
        return

    return func

class JoseImages(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)
        self.image_directories = {
            'test': test_generator,
        }

        self.boards = {
            'hypnohub': img_function(HYPNOHUB_CONFIG),
            'yandere': img_function(YANDERE_CONFIG),
            'e621': img_function(E621_CONFIG),
            'derpibooru': img_function(DERPIBOORU_CONFIG),
        }

    async def ext_load(self):
        return True, ''

    async def ext_unload(self):
        return True, ''

    async def json_api(self, cxt, boardid, config):
        '''
        {
            'search_term': stuff to search,
            'index_url': where are the latest posts,
            'search_url': search for stuff(defaults to index_url),
            'show_url': get individual posts,
            'post_key': where to get the post image URL,
            'limit_key': what is the tag to limit results,
            'search_key': what is the tag to search in search_url,

            'list_key': where are the array of posts,
            'search_url_key': same thing as list_key but in search,
        }
        '''
        search_term = config.get('search_term')
        index_url = config.get('index_url')
        search_url = config.get('search_url', index_url)
        show_url = config.get('show_url')
        post_key = config.get('post_key')

        limit_key = config.get('limit_key', 'limit')
        search_key = config.get('search_key', 'tags')
        list_key = config.get('list_key', None)
        search_url_key = config.get('search_url_key', None)
        random_flag = False

        if search_term == '-latest':
            # get latest
            await cxt.say('`[img.%s] most recent posts`', (boardid,))
            url = '%s?%s=%s' % (index_url, limit_key, IMAGE_LIMIT)
        elif search_term == '-random':
            # random id
            await cxt.say('`[img.%s] random ID`', (boardid,))
            random_flag = True
            url = '%s?%s=%s' % (index_url, limit_key, 1)
        else:
            # normally, search tags
            await cxt.say('`[img.%s] tags: %r`', (boardid, search_term))
            url = '%s?%s=%s&%s=%s' % (search_url, limit_key, IMAGE_LIMIT,\
                search_key, search_term)
            if search_key:
                list_key = search_url_key

        self.logger.info("images: json_api->%s: %r", boardid, search_term)
        response = await self.json_from_url(url)

        if not response:
            await cxt.say("`[img.%s] Error parsing JSON response, got %d bytes`", \
                (boardid, len(response)))
            return

        if list_key:
            response = response[list_key]

        post = None
        if random_flag:
            if not show_url:
                await cxt.say("`[img.%s] API doesn't support individual posts`", (boardid,))
                return

            most_recent_id = response[0]['id']

            try:
                random_id = random.randint(1, int(most_recent_id))
            except Exception as e:
                await cxt.say("`%r`", (e,))
                return

            random_post_url = '%s?id=%s' % (show_url, random_id)
            post = await self.jsom_from_url(random_post_url)
        else:
            if len(response) < 1:
                await cxt.say("`[img.%s] No results found.`", (boardid,))
                return
            post = random.choice(response)

        post_url = post[post_key]
        if ('hypnohub' in post_url) or ('derpi' in post_url):
            post_url = post_url.replace('//', '/')
            post_url = 'http:/%s' % post_url

        await cxt.say('ID: %s, URL: %s', (str(post['id']), str(post_url)))
        return

    async def img_routine(self, cxt):
        channel_id = await jcommon.configdb_get(cxt.message.server.id, 'imgchannel')

        if channel_id is None:
            raise je.CommonError("No channel is set for image commands, use `j!imgchannel`.")

        if cxt.message.channel.id != channel_id:
            raise je.CommonError("You aren't in a image channel")

        res = await self.jcoin_pricing(cxt, jcommon.IMG_PRICE)
        return res

    async def do_board(self, cxt, board_id, args):
        access = await self.img_routine(cxt)
        if access:
            try:
                search_terms = ' '.join(args[1:])
                self.logger.info("[do_board:%s]: %r", board_id, search_terms)
                await self.boards[board_id](self.json_from_url, cxt, search_terms)
            except Exception as err:
                await cxt.say("`ERROR: %s`", (traceback.format_exc(),))

    async def c_hypno(self, message, args, cxt):
        await self.do_board(cxt, 'hypnohub', args)

    async def c_yandere(self, message, args, cxt):
        await self.do_board(cxt, 'yandere', args)

    async def c_e621(self, message, args, cxt):
        await self.do_board(cxt, 'e621', args)

    async def c_derpibooru(self, message, args, cxt):
        await self.do_board(cxt, 'derpibooru', args)

    async def c_derpi(self, message, args, cxt):
        await self.c_derpibooru(message, args, cxt)

    async def c_urban(self, message, args, cxt):
        '''`j!urban stuff` - Urban Dictionary'''
        term = ' '.join(args[1:])

        await self.jcoin_pricing(cxt, jcommon.API_TAX_PRICE)

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

    async def c_random(self, message, args, cxt):
        '''`j!random directory|"list"` - Random images from some sources here and there'''

        if len(args) < 2:
            await cxt.say(self.c_random.__doc__)
            return

        try:
            directory = args[1]
        except:
            await cxt.say("Error parsing `directory`")
            pass

        if directory == 'list':
            await cxt.say(self.codeblock('', ', '.join(\
                self.image_directories.keys())))
            return

        generator = self.image_directories.get(directory)
        if generator is None:
            await cxt.say("Directory `%r` not found.", (directory,))
            return

        url = await generator()
        await cxt.say(url)
