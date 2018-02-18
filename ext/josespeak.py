#!/usr/bin/env python3

import os
import random
import subprocess
import time
import asyncio
import discord
import sys
sys.path.append("..")
import josecommon as jcommon
import joseerror as je

from midiutil.MidiFile import MIDIFile
import markovify
import ext.letters as letters

logger = None
PROB_FULLWIDTH_TEXT = 0.1
MESSAGE_LIMIT = 3000
LETTER_TO_PITCH = jcommon.LETTER_TO_PITCH

SPEAK_TRIGGER_PREFIX = 'jose '
SPEAK_PREFIXES = ['jose ', 'josé ']
GOOD_TEXT_PROBABILITY = 0.7

async def make_texter(textpath=None, markov_length=2, text=None):
    texter = NewTexter(textpath, markov_length, text)
    await texter.mktexter()
    return texter

def make_textmodel(textdata, markov_length):
    tmodel = markovify.NewlineText(textdata, markov_length)
    return tmodel

def get_sentence(textmodel, char_limit=None):
    text = 'None'
    if char_limit is not None:
        text = textmodel.make_short_sentence(char_limit)
    else:
        text = textmodel.make_sentence()

    return text

class NewTexter:
    def __init__(self, textpath, markov_length, text, loop=None):
        self.refcount = 1
        self.markov_length = markov_length
        self.textdata = ''

        # custom asyncio event loop
        self.loop = loop
        if self.loop is None:
            self.loop = asyncio.get_event_loop()

        if textpath is None:
            self.textdata = text
        else:
            with open(textpath, 'r') as textfile:
                self.textdata = textfile.read()

        self.text_model = None

    async def mktexter(self):
        t_start = time.time()

        future_textmodel = self.loop.run_in_executor(None, make_textmodel, \
            self.textdata, self.markov_length)

        self.text_model = await future_textmodel

        t_taken = (time.time() - t_start) * 1000
        if logger:
            logger.info("NewTexter: mktexter took %.2fms", t_taken)
        else:
            print("NewTexter: mktexter took %.2fms" % t_taken)

    def __repr__(self):
        return 'Texter(refcount=%s)' % self.refcount

    async def gen_sentence(self, char_limit=None):
        if self.refcount <= 4:
            # max value refcount can be is 5
            self.refcount += 1

        res = None
        count = 0
        while res is None:
            if count > 3: break
            future_sentence = self.loop.run_in_executor(None, get_sentence, \
                self.text_model, char_limit)
            res = await future_sentence
            count += 1

        return str(res)

    async def clear(self):
        del self.text_model

class JoseSpeak(jcommon.Extension):
    def __init__(self, _client):
        global logger
        jcommon.Extension.__init__(self, _client)
        logger = self.logger

        self.flag = False

        self.text_generators = {}
        self._locks = {}

        self.last_texter_mcount = -1
        self.last_texter_time = -1

        # every minute
        self.cbk_new('jspeak.texter_collection', self.texter_collection, 60)

    async def ext_load(self):
        try:
            # make generators
            self.cult_generator = await make_texter('db/jose-data.txt', 1)

            return True, ''
        except Exception as e:
            return False, repr(e)

    async def ext_unload(self):
        try:
            self.text_generators.clear()

            # Remove the callbacks
            self.cbk_remove('jspeak.texter_collection')

            return True, ''
        except Exception as e:
            return False, repr(e)

    async def server_messages(self, serverid, limit=MESSAGE_LIMIT):
        server = self.client.get_server(serverid)
        channel_id = await jcommon.configdb_get(serverid, 'speak_channel')
        channel = None
        try:
            if len(channel_id) > 0:
                channel = server.get_channel(channel_id)
            else:
                channel = server.default_channel
        except:
            channel = server.default_channel

        if channel is None:
            self.logger.warning("channel %r is None", channel_id)
            return 'None'

        logs = self.client.logs_from(channel, limit)
        botblock = await jcommon.configdb_get(serverid, 'botblock')

        messages = []
        try:
            async for message in logs:
                author = message.author
                if author.id == jcommon.JOSE_ID:
                    continue

                if author.bot and botblock:
                    continue

                filtered = jcommon.speak_filter(message.clean_content)
                messages.append(filtered)
        except discord.Forbidden:
            self.logger.info(f'got Forbidden from {serverid}')
            del server, logs, botblock, channel
            return ['None']

        del server, logs, botblock, channel
        return messages

    async def server_messages_string(self, serverid, limit=None):
        r = await self.server_messages(serverid, limit)
        return '\n'.join(r)

    async def new_generator(self, serverid, limit=None):
        # create one Texter, for one server
        lock = self._locks.get(serverid)
        if lock:
            await asyncio.sleep(8)
            if serverid in self.text_generators:
                return self.text_generators[serverid]

        # set lock
        self._locks[serverid] = True

        t_start = time.time()

        messages = await self.server_messages(serverid, limit)

        if serverid in self.text_generators:
            # delet this
            await self.text_generators[serverid].clear()

        # create it
        _joined = '\n'.join(messages)
        self.text_generators[serverid] = await make_texter(None, 1, _joined)

        # wordcount lol
        self.last_texter_mcount = _joined.count(' ') + 1
        self.last_texter_time = (time.time() - t_start)
        self._locks[serverid] = False

        return True

    async def texter_collection(self):
        if len(self.text_generators) <= 0:
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
            lentg = len(self.text_generators)

            for serverid in sid_to_clear:
                del self.text_generators[serverid]

            time_taken_ms = (time.time() - t_start) * 1000
            self.logger.info("%d down to %d Texters in %.3fms", lentg, \
                (lentg - deadtexters), time_taken_ms)

            del sid_to_clear, t_start, time_taken_ms

    async def c_speaktrigger(self, message, args, cxt):
        """`j!speaktrigger` - trigger jose's speaking code"""
        if message.server is None:
            raise je.CommonError("DMs don't have `j!speaktrigger` support")

        cxt.env['flag'] = True
        cxt.env['flat_fw'] = False
        if 'fw' in args:
            cxt.env['flag_fw'] = True
        await self.e_on_message(message, cxt)

    async def c_experimental(self, message, args, cxt):
        '''`j!experimental` - **DON'T USE THIS**'''
        await self.is_admin(message.author.id)

        try:
            msglimit = int(args[1])
        except:
            msglimit = 1000

        await cxt.send_typing()

        if msglimit > 10000:
            await cxt.say("no")
            return

        logs = self.client.logs_from(message.channel, limit=msglimit)
        res = []
        async for message in logs:
            if message.author != jcommon.JOSE_ID:
                res.append(jcommon.speak_filter(message.clean_content))

        texter = await make_texter(None, 1, '\n'.join(res))

        result = await texter.gen_sentence()
        await cxt.say(result)

        del texter, result, res, logs

    async def c_spt(self, message, args, cxt):
        '''`j!spt` - alias for `!speaktrigger`'''
        await self.c_speaktrigger(message, args, cxt)

    async def c_ntexter(self, message, args, cxt):
        '''`j!ntexter serverid1 serverid2 ...` - Create Texters'''
        await self.is_admin(message.author.id)

        try:
            servers = args[1:]
        except:
            await cxt.say(self.c_ntexter.__doc__)
            return

        t_start = time.time()
        total_lines = 0
        for serverid in servers:
            ok = await self.new_generator(serverid, MESSAGE_LIMIT)
            total_lines += self.last_texter_mcount
            if not ok:
                await cxt.say(":poop: Error creating Texter for %s", (serverid,))
                return

        t_taken = (time.time() - t_start) * 1000

        await cxt.say("`Created %d Texters with %d words in total. Took %.2fms`", \
            (len(servers), total_lines, t_taken))

    async def c_texclean(self, message, args, cxt):
        await self.is_admin(message.author.id)

        try:
            times = int(args[1])
        except:
            times = 1

        oldamount = len(self.text_generators)

        t_start = time.time()

        for i in range(times):
            await self.texter_collection()

        t_taken = (time.time() - t_start) * 1000

        newamount = len(self.text_generators)

        await cxt.say("`Took %.5fms cleaning %d times, from %d I now have %d, cleaned %d`", \
            (t_taken, times, oldamount, newamount, oldamount - newamount))

    async def c_texstat(self, message, args, cxt):
        '''`j!texstat` - Texter Stats'''
        svcount = len(self.client.servers)
        report = """%d/%d Texters loaded
 * Last Texter made had %d words, took %.2fms to load it"""

        res = report % (len(self.text_generators), svcount, \
            self.last_texter_mcount, (self.last_texter_time * 1000))

        await cxt.say(self.codeblock("", res))

    async def e_on_message(self, message, cxt):
        sid = message.server.id

        probability = await jcommon.configdb_get(sid, 'speak_prob')
        if probability is None:
            self.logger.error("[WTF] probability = None for server %s", sid)
            return

        random_chance = False
        in_conversation = False

        if probability > 0:
            # don't spend random calls when probability is 0
            if random.random() < probability:
                random_chance = True

        _content = message.clean_content.lower()
        for prefix in SPEAK_PREFIXES:
            if _content.startswith(prefix):
                statement = _content[len(prefix):]
                pb_english = letters.english_probability(statement)
                if pb_english >= GOOD_TEXT_PROBABILITY:
                    in_conversation = True

        if random_chance or cxt.env.get('flag', False) or in_conversation:
            await cxt.send_typing()

            # ensure the server already has its texter loaded up
            if sid not in self.text_generators:
                await self.new_generator(sid, MESSAGE_LIMIT)

            await self.speak(self.text_generators[sid], cxt)

    async def server_sentence(self, serverid, length=None, flag_fw=False):
        if serverid not in self.text_generators:
            await self.new_generator(serverid, MESSAGE_LIMIT)

        texter = self.text_generators[serverid]
        res = await texter.gen_sentence(length)

        fw_probability = await jcommon.configdb_get(serverid, 'fw_prob', 0.1)

        if random.random() < fw_probability or flag_fw:
            res = res.translate(jcommon.WIDE_MAP)

        return res

    async def speak(self, texter, cxt):
        res = await texter.gen_sentence()

        fw_probability = await jcommon.configdb_get(cxt.message.server.id, 'fw_prob', 0.1)

        if random.random() < fw_probability or cxt.env.get('flag_fw', False):
            res = res.translate(jcommon.WIDE_MAP)

        await cxt.say(res)

    async def c_falar(self, message, args, cxt):
        """`j!falar` - josé fala"""
        await self.speak(self.cult_generator, cxt)

    async def c_josetxt(self, message, args, cxt):
        '''`j!josetxt` - Mostra a quantidade de linhas, palavras e bytes no db/jose-data.txt'''
        output = subprocess.Popen(['wc', 'db/jose-data.txt'], stdout=subprocess.PIPE).communicate()[0]
        await cxt.say(output)

    async def say_prefixed(self, cxt, prefix):
        await cxt.send_typing()
        ecxt = jcommon.EmptyContext(self.client, cxt.message)
        await self.c_speaktrigger(cxt.message, [], ecxt)
        res = await ecxt.getall()
        await cxt.say(f'{prefix}{res}')

    async def c_jwormhole(self, message, args, cxt):
        '''`j!jwormhole` - `j!speaktrigger` routed to Septapus Wormhole'''
        await self.say_prefixed(cxt, '<@127296623779774464> wormhole send ')

    async def c_tatsu(self, message, args, cxt):
        '''`j!tatsu` - `j!speaktrigger` rerouted to prefix with `^``'''
        await self.say_prefixed(cxt, '^')

    async def c_skprefix(self, message, args, cxt):
        '''`j!skprefix prefix` - prefix shit jose says'''
        try:
            prefix = args[1]
        except:
            await cxt.say(self.c_skprefix.__doc__)
            return

        await self.say_prefixed(cxt, prefix)

    async def c_jw(self, message, args, cxt):
        '''`j!jw` - alias para `!jwormhole`'''
        await self.c_jwormhole(message, args, cxt)

    async def c_madlibs(self, message, args, cxt):
        '''`j!madlibs succ my ---` - changes any `---` in input to a 12-letter sentence'''

        if len(args) < 2:
            await cxt.say(self.c_madlibs.__doc__)
            return

        serverid = message.server.id
        res = []

        await cxt.send_typing()

        strrep = ' '.join(args[1:])
        if strrep.count('---') < 1:
            await cxt.say(":no_entry_sign: you can't just make josé say whatever you want! :no_entry_sign:")
            return

        if strrep.count('---') > 5:
            await cxt.say("thats a .......... lot")
            return

        for word in args[1:]:
            if word == '---':
                res.append(await self.server_sentence(serverid, 12))
            else:
                res.append(jcommon.speak_filter(word))

        self.logger.info("madlibs: %s => %s", res, ' '.join(res))

        await cxt.say(' '.join(res))

    async def make_midi(self, tempo_to_use, string):
        midi_file = MIDIFile(1)
        track = 0
        st_time = 0
        midi_file.addTrackName(track, st_time, "Jose")
        midi_file.addTempo(track, st_time, tempo_to_use)

        # add some notes
        channel = 0
        volume = 100
        duration = 1
        st_time = 0

        self.logger.info("Making MIDI out of %r", string)

        # do the magic
        for index, letter in enumerate(string):
            if letter in LETTER_TO_PITCH:
                # get letter after the letter
                try:
                    modifier = string[index + 1]
                    if modifier == " ": duration = 2
                    elif modifier == ",": duration = 3
                    elif modifier == ".": duration = 4
                    else: duration = 1
                except IndexError:
                    duration = 1

                st_time += duration
                pitch = LETTER_TO_PITCH[letter]

                # run that in a thread
                future = self.loop.run_in_executor(None, midi_file.addNote, \
                    track, channel, pitch, st_time, duration, volume)
                await future

        return midi_file

    async def c_midi(self, message, args, cxt):
        '''`j!midi [stuff]` - Make MIDI files made out of josé's generated sentences
        `j!midi bpm<bpm> [stuff]` - set tempo'''
        if message.server is None:
            await cxt.say("Esse comando não está disponível em DMs")
            return

        t_start = time.time()

        await cxt.send_typing()
        res = ''
        tempo_to_use = 120

        ecxt = jcommon.EmptyContext(self.client, message)
        await self.c_speaktrigger(message, [], ecxt)
        generated_str = await ecxt.getall()

        try:
            if args[1].startswith('bpm'):
                bpmval = args[1][len('bpm'):]
                try:
                    tempo_to_use = int(bpmval)
                except ValueError:
                    await cxt.say("Sorry, but `%r` isn't a valid integer for BPM.", \
                        (bpmval,))
                    return
        except IndexError:
            pass

        if len(args) > 1:
            if tempo_to_use == 120:
                res = ' '.join(args[1:])
            else:
                res = ' '.join(args[2:])
        else:
            res = generated_str

        midi_file = await self.make_midi(tempo_to_use, res)

        t_taken_ms = (time.time() - t_start) * 1000
        self.logger.info("Took %.2fms to make MIDI file", t_taken_ms)

        fname = '%s.mid' % generated_str
        with open(fname, 'wb') as outf:
            future = self.loop.run_in_executor(None, midi_file.writeFile, outf)
            await future

        # send file
        await self.client.send_file(message.channel, fname, \
            content=('took %.2fms to do that' % t_taken_ms))

        os.remove(fname)
