#!/usr/bin/env python3

import os
import random
import subprocess
import json
import time
import asyncio
import sys
sys.path.append("..")
import josecommon as jcommon

from midiutil.MidiFile import MIDIFile
import markovify

logger = None
PROB_FULLWIDTH_TEXT = 0.32
MESSAGE_LIMIT = 10000 # 10k messages
LETTER_TO_PITCH = jcommon.LETTER_TO_PITCH

async def make_texter(textpath=None, markov_length=2, text=None):
    texter = NewTexter(textpath, markov_length, text)
    await texter.mktexter()
    return texter

def make_textmodel(textdata, markov_length):
    tmodel = markovify.NewlineText(textdata, markov_length)
    return tmodel

def get_sentence(textmodel):
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

    async def gen_sentence(self, word_limit=None):
        if self.refcount <= 2:
            # max value refcount can be is 3
            self.refcount += 1

        res = None
        count = 0
        while res is None:
            if count > 3: break
            future_sentence = self.loop.run_in_executor(None, get_sentence, \
                self.text_model)
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
        self.wlengths = {}
        self.messages = {}
        self.text_lengths = {}
        self.msgcount = {}
        self.txcleaned = -1

        self.last_texter_mcount = -1
        self.last_texter_time = -1

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

    async def ext_load(self):
        try:
            self.text_generators = {}
            self.text_lengths = {}

            # make generators
            self.cult_generator = await make_texter('db/jose-data.txt', 1)
            self.global_generator = await make_texter('db/zelao.txt', 1)

            # load things in files
            self.wlengths = json.load(open(self.db_length_path, 'r'))
            self.messages = json.load(open(self.db_msg_path, 'r'))

            return True, ''
        except Exception as e:
            return False, repr(e)

    async def ext_unload(self):
        try:
            # save DB
            await self.save_databases()

            # clear the dict full of shit (it rhymes)
            self.text_generators.clear()

            # Remove the callbacks
            self.cbk_remove('jspeak.texter_collection')
            self.cbk_remove('jspeak.savedb')

            return True, ''
        except Exception as e:
            return False, repr(e)

    async def server_messages(self, serverid, limit=None):
        cur = await self.dbapi.do('SELECT message FROM markovdb WHERE serverid=?', (serverid,))
        rows = [row[0] for row in cur.fetchall()]
        if limit is not None:
            pos = len(rows) - limit
            rows = rows[pos:]

        return rows

    async def server_messages_string(self, serverid, limit=None):
        r = await self.server_messages(serverid, limit)
        return '\n'.join(r)

    async def new_generator(self, serverid, limit=None):
        # create one Texter, for one server
        t_start = time.time()

        messages = await self.server_messages(serverid, limit)
        self.msgcount[serverid] = len(messages)

        if serverid in self.text_generators:
            # delet this
            await self.text_generators[serverid].clear()

        # create it
        self.text_generators[serverid] = await make_texter(None, 1, '\n'.join(messages))

        self.last_texter_mcount = self.msgcount[serverid]
        self.last_texter_time = (time.time() - t_start)

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
            self.txcleaned = deadtexters
            lentg = len(self.text_generators)
            logger.info("%d down to %d Texters", lentg, \
                (lentg - deadtexters))

            for serverid in sid_to_clear:
                del self.text_generators[serverid]

            time_taken_ms = (time.time() - t_start) * 1000
            logger.info("Texter cleaning took %.4fms", time_taken_ms)

            del sid_to_clear, t_start, time_taken_ms

    async def save_databases(self):
        self.logger.info("savedb:speak")
        json.dump(self.wlengths, open(self.db_length_path, 'w'))
        json.dump(self.messages, open(self.db_msg_path, 'w'))

    async def c_savedb(self, message, args, cxt):
        """`j!savedb` - saves all available databases(autosaves every 3 minutes)"""
        await self.is_admin(message.author.id)

        await self.save_databases()
        await cxt.say(":floppy_disk: saved messages database :floppy_disk:")

    async def c_speaktrigger(self, message, args, cxt):
        """`j!speaktrigger` - trigger jose's speaking code"""
        cxt.env['flag'] = True
        await self.e_on_message(message, cxt)

    async def c_spt(self, message, args, cxt):
        '''`j!spt` - alias para `!speaktrigger`'''
        await self.c_speaktrigger(message, args, cxt)

    async def c_ntexter(self, message, args, cxt):
        '''`j!ntexter serverid1 serverid2 ...` - Create Texters **[ADMIN COMMAND]**'''
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

        await cxt.say("`Created %d Texters with %d lines in total. Took %.2fms`", \
            (len(servers), total_lines, t_taken))

    async def c_texclean(self, message, args, cxt):
        await self.is_admin(message.author.id)

        oldamount = len(self.text_generators)

        t_start = time.time()
        await self.texter_collection()
        t_taken = (time.time() - t_start) * 1000

        newamount = len(self.text_generators)

        await cxt.say("`Took %.5fms cleaning %d Texters out of %d, now I have %d`", \
            (t_taken, oldamount - newamount, oldamount, newamount))

    async def c_texstat(self, message, args, cxt):
        '''`j!texstat` - Texter Stats'''
        svcount = len(self.client.servers)
        report = """%d/%d Texters loaded
 * Last Texter made had %d lines, took %.2fms to load it"""

        res = report % (len(self.text_generators), svcount, \
            self.last_texter_mcount, (self.last_texter_time * 1000))

        await cxt.say(self.codeblock("", res))

    async def e_on_message(self, message, cxt):
        if message.server is None:
            # ignore DMs here as well
            return

        # filter message before adding
        filtered_msg = jcommon.speak_filter(message.content)
        sid = message.server.id

        if message.server.id not in self.wlengths:
            # average wordlength
            self.wlengths[sid] = 5

        if message.server.id not in self.messages:
            # the message being received now
            self.messages[sid] = 1

        # get word count
        self.wlengths[sid] += len(filtered_msg.split())
        self.messages[sid] += 1

        # recalc
        self.text_lengths[sid] = \
            self.wlengths[sid] / self.messages[sid]

        for line in filtered_msg.split('\n'):
            # append every line to the database
            # filter lines before adding
            filtered_line = jcommon.speak_filter(line)
            if len(filtered_line) > 0:
                # no issues, add it
                await self.dbapi.do("INSERT INTO markovdb (serverid, message) \
                    VALUES (?, ?)", (sid, filtered_line))

        if random.random() < 0.03 or cxt.env.get('flag', False):
            await cxt.send_typing()

            # default 5 words
            length = 5
            if sid in self.text_lengths:
                length = int(self.text_lengths[sid])

            # ensure the server already has its texter loaded up
            if sid not in self.text_generators:
                await self.new_generator(sid, MESSAGE_LIMIT)

            await self.speak(self.text_generators[sid], length, cxt)

    async def speak(self, texter, length_words, cxt):
        res = await texter.gen_sentence(length_words)
        if random.random() < PROB_FULLWIDTH_TEXT:
            res = res.translate(jcommon.WIDE_MAP)
        await cxt.say(res)

    async def c_falar(self, message, args, cxt):
        """`j!falar [wordmax]` - josé fala(wordmax default 10)"""
        wordlength = 10

        if len(args) > 2:
            if int(args[1]) > 100:
                await cxt.say("Nope :tm:")
                return
            else:
                wordlength = int(args[1])

        await self.speak(self.cult_generator, wordlength, cxt)

    async def c_sfalar(self, message, args, cxt):
        """`j!sfalar [wordmax]` - falar usando textos do seu servidor atual(wordmax default 10)"""
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
        """`j!gfalar [wordmax]` - falar usando o texto global(wordmax default 10)"""
        wordlength = 10

        if len(args) > 2:
            if int(args[1]) > 100:
                await cxt.say("Nope :tm:")
                return
            else:
                wordlength = int(args[1])

        await self.speak(self.global_generator, wordlength, cxt)

    async def c_josetxt(self, message, args, cxt):
        '''`j!josetxt` - Mostra a quantidade de linhas, palavras e bytes no db/jose-data.txt'''
        output = subprocess.Popen(['wc', 'db/jose-data.txt'], stdout=subprocess.PIPE).communicate()[0]
        await cxt.say(output)

    async def c_zelaotxt(self, message, args, cxt):
        '''`j!zelaotxt` - Mostra a quantidade de linhas, palavras e bytes no db/zelao.txt'''
        output = subprocess.Popen(['wc', 'db/zelao.txt'], stdout=subprocess.PIPE).communicate()[0]
        await cxt.say(output)

    async def c_jwormhole(self, message, args, cxt):
        '''`j!jwormhole` - `j!speaktrigger` routed to Septapus Wormhole'''
        if message.server is None:
            await cxt.say("Esse comando não está disponível em DMs")
            return

        await cxt.send_typing()
        ecxt = jcommon.EmptyContext(self.client, message)
        await self.c_speaktrigger(message, [], ecxt)
        res = await ecxt.getall()
        await cxt.say("<@127296623779774464> wormhole send %s", (res,))

    async def c_tatsu(self, message, args, cxt):
        '''`j!tatsu` - `j!speaktrigger` rerouted to prefix with `^``'''
        if message.server is None:
            await cxt.say("DMs not available")
            return

        await cxt.send_typing()
        ecxt = jcommon.EmptyContext(self.client, message)
        await self.c_speaktrigger(message, [], ecxt)
        res = await ecxt.getall()
        await cxt.say("^%s", (res,))

    async def c_jw(self, message, args, cxt):
        '''`j!jw` - alias para `!jwormhole`'''
        await self.c_jwormhole(message, args, cxt)

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

        self.logger.info("Making MIDI out of %r", res)

        # do the magic
        for index, letter in enumerate(res):
            if letter in LETTER_TO_PITCH:
                # get letter after the letter
                try:
                    modifier = res[index + 1]
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
