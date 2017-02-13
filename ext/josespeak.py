#!/usr/bin/env python3

import sys
sys.path.append("..")
import josecommon as jcommon

import re
import random
import subprocess
import json
import io
import time

logger = None
MESSAGE_LIMIT = 10000 # 10k messages

def fixCaps(word):
    if word.isupper() and (word != "I" or word != "Eu"):
        word = word.lower()
    elif word[0].isupper():
        word = word.lower().capitalize()
    else:
        word = word.lower()
    return word

def toHashKey(lst):
    return tuple(lst)

def wordlist(filename, file_object=None):
    if file_object is None:
        file_object = open(filename, 'r')

    wordlist = [fixCaps(w) for w in re.findall(r"[\w']+|[.,!?;]", file_object.read())]
    file_object.close()
    return wordlist

class Texter:
    def __init__(self, textpath, markov_length, text=None):
        self.tempMapping = {}
        self.mapping = {}
        self.starts = []
        self.refcount = 0

        if textpath is None:
            text_object = io.StringIO(text)
            self.build_mapping(wordlist(None, text_object), markov_length)
        else:
            self.build_mapping(wordlist(textpath), markov_length)

    def __repr__(self):
        return 'Texter(refcount=%d)' % self.refcount

    def add_temp_mapping(self, history, word):
        while len(history) > 0:
            first = toHashKey(history)
            if first in self.tempMapping:
                if word in self.tempMapping[first]:
                    self.tempMapping[first][word] += 1.0
                else:
                    self.tempMapping[first][word] = 1.0
            else:
                self.tempMapping[first] = {}
                self.tempMapping[first][word] = 1.0
            history = history[1:]

    def build_mapping(self, wordlist, markovLength):
        self.starts.append(wordlist[0])
        for i in range(1, len(wordlist) - 1):
            if i <= markovLength:
                history = wordlist[: i + 1]
            else:
                history = wordlist[i - markovLength + 1 : i + 1]
            follow = wordlist[i + 1]
            # if the last elt was a period, add the next word to the start list
            if history[-1] == "." and follow not in ".,!?;":
                self.starts.append(follow)
            self.add_temp_mapping(history, follow)

        # Normalize the values in tempMapping, put them into mapping
        for first, followset in self.tempMapping.items():
            total = sum(followset.values())
            # Normalizing here:
            self.mapping[first] = dict([(k, v / total) for k, v in followset.items()])

    def next_word(self, prevList):
        sum = 0.0
        retval = ""
        index = random.random()
        # Shorten prevList until it's in mapping
        while toHashKey(prevList) not in self.mapping:
            if len(prevList) == 0:
                logger.error("Texter.next_word: len(prevList) == 0")
                return None
            else:
                prevList.pop(0)

        # Get a random word from the mapping, given prevList
        for k, v in self.mapping[toHashKey(prevList)].items():
            sum += v
            if sum >= index and retval == "":
                retval = k

        return retval

    async def gen_sentence(self, markovLength, word_limit):
        # Start with a random "starting word"
        curr = random.choice(self.starts)
        sent = curr.capitalize()
        prevList = [curr]
        word_count = 0
        # Keep adding words until we hit a period
        while (curr not in "."):
            if word_count > word_limit:
                break
            curr = self.next_word(prevList)

            if curr is None:
                # fallback behavior
                return 'None'

            prevList.append(curr)

            # if the prevList has gotten too long, trim it
            if len(prevList) > markovLength:
                prevList.pop(0)

            if (curr not in ".,!?;"):
                sent += " " # Add spaces between words (but not punctuation)

            sent += curr
            word_count += 1

        if self.refcount <= 2:
            # max value refcount can be is 3
            self.refcount += 1

        return sent

    async def clear(self):
        # clear the stuff, or at least signal Python to remove them
        del self.tempMapping, self.mapping, self.starts

class JoseSpeak(jcommon.Extension):
    def __init__(self, cl):
        global logger
        jcommon.Extension.__init__(self, cl)
        self.cult_generator = Texter('db/jose-data.txt', 1)
        self.global_generator = Texter('db/zelao.txt', 1)
        logger = self.logger

        self.flag = False

        self.text_generators = {}
        self.wlengths = {}
        self.messages = {}
        self.text_lengths = {}
        self.msgcount = {}
        self.txcleaned = -1

        self.db_length_path = jcommon.MARKOV_LENGTH_PATH
        self.db_msg_path = jcommon.MARKOV_MESSAGES_PATH

        self.dbapi._register("markovdb", """CREATE TABLE IF NOT EXISTS markovdb (
            serverid nvarchar(90),
            message nvarchar(2050)
        );""")

        # load timers

        # every 3 minutes
        self.cbk_new('jspeak.savedb', self.save_databases, 180)

        # every minute
        self.cbk_new('jspeak.texter_collection', self.texter_collection, 60)

    async def server_messages(self, serverid, limit=None):
        cur = await self.dbapi.do('SELECT message FROM markovdb WHERE serverid=?', (serverid,))
        r = [row[0] for row in cur.fetchall()]
        if limit is not None:
            r = r[:limit]

        return r

    async def server_messages_string(self, serverid, limit=None):
        r = await self.server_messages(serverid, limit)
        return '\n'.join(r)

    async def new_generator(self, serverid, limit=None):
        # create one Texter, for one server
        messages = await self.server_messages(serverid, limit)
        self.msgcount[serverid] = len(messages)

        if serverid in self.text_generators:
            # delet this
            await self.text_generators[serverid].clear()

        # create it
        self.text_generators[serverid] = Texter(None, 1, '\n'.join(messages))
        return True

    async def texter_collection(self):

        if len(self.text_generators) <= 0:
            logger.debug("no texters available")
            return

        t_start = time.time()
        sid_to_clear = []

        for serverid in self.text_generators:
            texter = self.text_generators[serverid]
            if texter.refcount <= 0:
                await texter.clear()
                sid_to_clear.append(serverid)
            else:
                texter.refcount -= 1

        deadtexters = len(sid_to_clear)
        if deadtexters > 0:
            self.txcleaned = deadtexters
            logger.info("Cleaning %d dead Texters, was %d", deadtexters, \
                len(self.text_generators))

        for serverid in sid_to_clear:
            del self.text_generators[serverid]

        time_taken_ms = (time.time() - t_start) * 1000
        logger.info("Texter cleaning took %.4fms", time_taken_ms)

        del sid_to_clear, t_start, time_taken_ms

    async def save_databases(self):
        self.logger.info("Save josespeak database")
        json.dump(self.wlengths, open(self.db_length_path, 'w'))
        json.dump(self.messages, open(self.db_msg_path, 'w'))

    async def c_savedb(self, message, args, cxt):
        """`!savedb` - saves all available databases(autosaves every 3 minutes)"""
        await self.is_admin(message.author.id)

        await self.save_databases()
        await cxt.say(":floppy_disk: saved messages database :floppy_disk:")

    async def c_speaktrigger(self, message, args, cxt):
        """`!speaktrigger` - trigger jose's speaking code"""
        self.flag = True
        await self.e_on_message(message, cxt)

    async def c_spt(self, message, args, cxt):
        '''`!spt` - alias para `!speaktrigger`'''
        await self.c_speaktrigger(message, args, cxt)

    async def ext_load(self):
        try:
            self.text_generators = {}
            self.text_lengths = {}

            # load things in files
            self.wlengths = json.load(open(self.db_length_path, 'r'))
            self.messages = json.load(open(self.db_msg_path, 'r'))

            return True, ''
        except Exception as e:
            return False, str(e)

    async def ext_unload(self):
        try:
            # save DB
            await self.save_databases()

            # clear the dict full of shit (it rhymes)
            self.text_generators.clear()

            # Remove the callbacks
            self.cbk_remove('jspeak.reload_texter')
            self.cbk_remove('jspeak.savedb')

            return True, ''
        except Exception as e:
            return False, str(e)

    async def c_getmsg(self, message, args, cxt):
        '''`!getmsg serverid amount`'''
        await self.is_admin(message.author.id)

        try:
            serverid = args[1]
            amount = args[2]
        except:
            await cxt.say(self.c_getmsg.__doc__)
            return

        msg = await self.server_messages(serverid, amount)
        await cxt.say(self.codeblock("python", repr(msg)))

    async def c_ntexter(self, message, args, cxt):
        '''`!ntexter serverid1 serverid2 ...` - Create Texters **[ADMIN COMMAND]**'''
        await self.is_admin(message.author.id)

        try:
            servers = args[1:]
        except:
            await cxt.say(self.c_ntexter.__doc__)
            return

        t_start = time.time()
        for serverid in servers:
            ok = await self.new_generator(serverid, MESSAGE_LIMIT)
            if not ok:
                await cxt.say(":poop: Error creating Texter for %s" % serverid)
                return

        t_taken = (time.time() - t_start) * 1000

        await cxt.say("`Created %d Texters. Took %.2fms`" % \
            (len(servers), t_taken))

    async def c_texclean(self, message, args, cxt):
        await self.is_admin(message.author.id)

        oldamount = len(self.text_generators)

        t_start = time.time()
        await self.texter_collection()
        t_taken = (time.time() - t_start) * 1000

        newamount = len(self.text_generators)

        await cxt.say("`Took %.5fms cleaning %d Texters out of %d`" % \
            (t_taken, oldamount - newamount, oldamount))

    async def c_texstat(self, message, args, cxt):
        '''`!texstat` - Texter Stats'''
        svcount = len(self.client.servers)
        await cxt.say("`%d/%d Texters loaded`" % \
            (len(self.text_generators), svcount))

    async def e_on_message(self, message, cxt):
        if message.server is None:
            # ignore DMs here as well
            return

        # filter message before adding
        filtered_msg = jcommon.speak_filter(message.content)

        if message.server.id not in self.wlengths:
            # average wordlength
            self.wlengths[message.server.id] = 5

        if message.server.id not in self.messages:
            # the message being received now
            self.messages[message.server.id] = 1

        # get word count
        self.wlengths[message.server.id] += len(filtered_msg.split())
        self.messages[message.server.id] += 1

        # recalc
        self.text_lengths[message.server.id] = self.wlengths[message.server.id] / self.messages[message.server.id]

        for line in filtered_msg.split('\n'):
            # append every line to the database
            # filter lines before adding
            filtered_line = jcommon.speak_filter(line)
            if len(filtered_line) > 0:
                # no issues, add it
                await self.dbapi.do("INSERT INTO markovdb (serverid, message) \
                    VALUES (?, ?)", (message.server.id, filtered_line))

        if random.random() < 0.03 or self.flag:
            self.flag = False
            # ensure the server already has its texter loaded up
            if message.server.id not in self.text_generators:
                await self.new_generator(message.server.id, MESSAGE_LIMIT)

            self.current = message
            await self.client.send_typing(message.channel)

            # default 5 words
            length = 5
            if message.server.id in self.text_lengths:
                length = int(self.text_lengths[message.server.id])

            await self.speak(self.text_generators[message.server.id], length, cxt)

    async def speak(self, texter, length_words, cxt):
        res = await texter.gen_sentence(1, length_words)
        await cxt.say(res)

    async def c_falar(self, message, args, cxt):
        """`!falar [wordmax]` - josé fala(wordmax default 10)"""
        wordlength = 10

        if len(args) > 2:
            if int(args[1]) > 100:
                await cxt.say("Nope :tm:")
                return
            else:
                wordlength = int(args[1])

        await self.speak(self.cult_generator, wordlength, cxt)

    async def c_sfalar(self, message, args, cxt):
        """`!sfalar [wordmax]` - falar usando textos do seu servidor atual(wordmax default 10)"""
        wordlength = 10

        if len(args) > 2:
            if int(args[1]) > 100:
                await cxt.say("Nope :tm:")
                return
            else:
                wordlength = int(args[1])

        # ensure Texter exists
        if message.server.id not in self.text_generators:
            await self.new_generator(message.server.id, MESSAGE_LIMIT)

        await self.speak(self.text_generators[message.server.id], wordlength, cxt)

    async def c_gfalar(self, message, args, cxt):
        """`!gfalar [wordmax]` - falar usando o texto global(wordmax default 10)"""
        wordlength = 10

        if len(args) > 2:
            if int(args[1]) > 100:
                await cxt.say("Nope :tm:")
                return
            else:
                wordlength = int(args[1])

        await self.speak(self.global_generator, wordlength, cxt)

    async def c_josetxt(self, message, args, cxt):
        '''`!josetxt` - Mostra a quantidade de linhas, palavras e bytes no db/jose-data.txt'''
        output = subprocess.Popen(['wc', 'db/jose-data.txt'], stdout=subprocess.PIPE).communicate()[0]
        await cxt.say(output)

    async def c_zelaotxt(self, message, args, cxt):
        '''`!zelaotxt` - Mostra a quantidade de linhas, palavras e bytes no db/zelao.txt'''
        output = subprocess.Popen(['wc', 'db/zelao.txt'], stdout=subprocess.PIPE).communicate()[0]
        await cxt.say(output)

    async def c_jwormhole(self, message, args, cxt):
        '''`!jwormhole` - Envia mensagens do !speaktrigger para o Wormhole do Septapus!'''
        if message.server is None:
            await cxt.say("Esse comando não está disponível em DMs")
            return

        ecxt = jcommon.EmptyContext(self.client, message)
        await self.c_speaktrigger(message, args, ecxt)
        res = await ecxt.getall()
        await cxt.say("<@127296623779774464> wormhole send %s" % res)

    async def c_jw(self, message, args, cxt):
        '''`!jw` - alias para `!jwormhole`'''
        await self.c_jwormhole(message, args, cxt)
