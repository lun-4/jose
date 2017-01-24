#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import josecommon as jcommon
import joseerror as je

import re
import random
import subprocess
import json
import io

def fixCaps(word):
    if word.isupper() and (word != "I" or word != "Eu"):
        word = word.lower()
    elif word [0].isupper():
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

        if textpath is None:
            text_object = io.StringIO(text)
            self.build_mapping(wordlist(None, text_object), markov_length)
        else:
            self.build_mapping(wordlist(textpath), markov_length)

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
                pass
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
            prevList.append(curr)

            # if the prevList has gotten too long, trim it
            if len(prevList) > markovLength:
                prevList.pop(0)

            if (curr not in ".,!?;"):
                sent += " " # Add spaces between words (but not punctuation)

            sent += curr
            word_count += 1
        return sent

class JoseSpeak(jcommon.Extension):
    def __init__(self, cl):
        jcommon.Extension.__init__(self, cl)
        self.cult_generator = Texter('jose-data.txt', 1)
        self.global_generator = Texter('zelao.txt', 1)

        self.flag = False

        self.database = {}
        self.text_generators = {}
        self.wlengths = {}
        self.messages = {}
        self.text_lengths = {}
        self.counter = 0

        self.database_path = jcommon.MARKOV_DB_PATH
        self.db_length_path = jcommon.MARKOV_LENGTH_PATH
        self.db_msg_path = jcommon.MARKOV_MESSAGES_PATH

        # load timers in async context
        asyncio.async(self._load_timer(), loop=self.loop)

    async def _load_timer(self):
        await self.textertimer()

    async def create_generators(self):
        for serverid in self.database:
            messages = self.database[serverid]
            self.logger.info("Generating Texter for server ID %s with %d messages", serverid, len(messages))
            self.text_generators[serverid] = Texter(None, 1, '\n'.join(messages))

        self.logger.info("Generated %d texters", len(self.text_generators))

    async def save_databases(self):
        self.logger.info("Saved databases")
        json.dump(self.database, open(self.database_path, 'w'))
        json.dump(self.wlengths, open(self.db_length_path, 'w'))
        json.dump(self.messages, open(self.db_msg_path, 'w'))

    async def c_savedb(self, message, args):
        """`!savedb` - saves all available databases(autosave for each 50 messages)"""
        await self.save_databases()
        await self.say(":floppy_disk: saved database :floppy_disk:")

    async def c_speaktrigger(self, message, args):
        """`!speaktrigger` - trigger jose's speaking code"""
        self.flag = True
        await self.e_on_message(message)

    async def ext_load(self):
        try:
            self.text_generators = {}
            self.text_lengths = {}

            # load things in files
            self.database = json.load(open(self.database_path, 'r'))
            self.wlengths = json.load(open(self.db_length_path, 'r'))
            self.messages = json.load(open(self.db_msg_path, 'r'))

            # make generators
            await self.create_generators()

            return True, ''
        except Exception as e:
            return False, str(e)

    async def ext_unload(self):
        try:
            await self.save_databases()
            self.text_generators.clear()

            return True, ''
        except Exception as e:
            return False, str(e)

    async def textertimer(self):
        while True:
            # wait 15 minutes to generate texters
            await asyncio.sleep(900)

            # should work
            await self.create_generators()

    async def c_forcereload(self, message, args):
        """`!forcereload` - save and load josespeak module"""
        ok = await self.ext_unload()
        if not ok[0]:
            await self.say('ext_unload :warning: ' % ok[1])

        ok = await self.ext_load()
        if not ok[0]:
            await self.say('ext_load :warning: ' % ok[1])

        await self.say("done")

    async def e_on_message(self, message):
        # store message in json database
        if message.server.id not in self.database:
            self.logger.info("New server in database: %s", message.server.id)
            self.database[message.server.id] = []

        # filter message before adding
        filtered_msg = jcommon.speak_filter(message.content)

        if message.server.id not in self.wlengths:
            self.wlengths[message.server.id] = 5

        if message.server.id not in self.messages:
            self.messages[message.server.id] = 1 # the message being received now

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
                self.logger.debug("add line %s", filtered_line)
                # print("add line %r" % filtered_line)
                self.database[message.server.id].append(filtered_line)

        # save everyone
        if (self.counter % 50) == 0:
            await self.save_databases()

        self.counter += 1

        if random.random() < 0.03 or self.flag:
            self.flag = False
            # ensure the server already has its database
            if message.server.id in self.text_generators:
                self.current = message
                await self.client.send_typing(message.channel)

                length = int(self.text_lengths[message.server.id])
                await self.speak(self.text_generators[message.server.id], length)

    async def speak(self, texter, length_words):
        res = await texter.gen_sentence(1, length_words)
        if jcommon.DEMON_MODE:
            res = res[::-1]
        elif jcommon.PARABENS_MODE:
            res = 'Parabéns %s' % res
        await self.say(res)

    async def c_falar(self, message, args):
        """`!falar [wordmax]` - josé fala(wordmax default 10)"""
        wordlength = 10

        if len(args) > 2:
            if int(args[1]) > 100:
                await self.say("Nope :tm:")
                return
            else:
                wordlength = int(args[1])

        await self.speak(self.cult_generator, wordlength)

    async def c_sfalar(self, message, args):
        """`!sfalar [wordmax]` - falar usando textos do seu servidor atual(wordmax default 10)"""
        wordlength = 10

        if len(args) > 2:
            if int(args[1]) > 100:
                await self.say("Nope :tm:")
                return
            else:
                wordlength = int(args[1])

        await self.speak(self.text_generators[message.server.id], wordlength)

    async def c_gfalar(self, message, args):
        """`!gfalar [wordmax]` - falar usando o texto global(wordmax default 10)"""
        wordlength = 10

        if len(args) > 2:
            if int(args[1]) > 100:
                await self.say("Nope :tm:")
                return
            else:
                wordlength = int(args[1])

        await self.speak(self.global_generator, wordlength)

    async def c_josetxt(self, message, args):
        '''`!josetxt` - Mostra a quantidade de linhas, palavras e bytes no jose-data.txt'''
        output = subprocess.Popen(['wc', 'jose-data.txt'], stdout=subprocess.PIPE).communicate()[0]
        await self.say(output)
