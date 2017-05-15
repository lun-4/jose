#!/usr/bin/env python3

import sys
import os
import json

sys.path.append("..")
import jauxiliar as jaux
import joseconfig as jconfig

import uuid

DEFAULT_MAGICWORD_DATABASE = '''
{}
'''

def parse(string, message):
    res = []
    i = 0
    while i < len(string):
        char = string[i]
        if char == '%' and string[i+1] == '%':
            res.append("%")
        elif char == '%' and string[i+1] == 'a':
            res.append("<@%s>" % message.author.id)
            i += 1
        else:
            res.append(char)
        i += 1

    return ''.join(res)

async def mw_response(magicword, message):
    return parse(magicword['response'], message)

async def mw_match(magicword, string):
    for word in magicword['words']:
        if word in string:
            return True

class JoseMagicWord(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)
        self.db_magicword_path = jconfig.MAGICWORD_PATH
        self.magicwords = {}
        self.counter = 0

    async def savedb(self):
        try:
            self.logger.debug("Saving Magicword database")
            json.dump(self.magicwords, open(self.db_magicword_path, 'w'))
        except Exception as err:
            self.logger.error("Error saving MW database: %r", err, exc_info=True)

    async def ext_load(self):
        try:
            self.magicwords = {}
            if not os.path.isfile(self.db_magicword_path):
                # recreate
                with open(self.db_magicword_path, 'w') as f:
                    f.write(DEFAULT_MAGICWORD_DATABASE)

            self.magicwords = json.load(open(self.db_magicword_path, 'r'))

            return True, ''
        except Exception as e:
            return False, str(e)

    async def ext_unload(self):
        try:
            await self.savedb()
            return True, ''
        except Exception as e:
            return False, str(e)

    async def e_on_message(self, message, cxt):
        if self.counter % 50 == 0:
            await self.savedb()

        if message.server is None:
            # ignore DMs
            return

        if message.server.id in self.magicwords:
            mwsdb = self.magicwords[message.server.id]
            for set_id in mwsdb:
                mw = mwsdb[set_id]
                match = await mw_match(mw, message.content.lower())
                if match:
                    response = await mw_response(mw, message)
                    await cxt.say(response, message.channel)
                    # No other magicwords should be done
                    return

        self.counter += 1

    async def c_setmw(self, message, args, cxt):
        '''`j!setmw magicword1,magicword2,magicword3;response` - Magic Words
        docs: https://github.com/lkmnds/jose/blob/master/doc/cmd/magicwords.md'''

        if len(args) < 2:
            await cxt.say(self.c_setmw.__doc__)
            return

        # get string that represents the magic word
        mwstr = ' '.join(args[1:])

        if ';' not in mwstr:
            await cxt.say("Malformed string")
            return

        # parse the string
        magicwords, mwresponse = mwstr.split(';')
        magicwords = magicwords.split(',')
        mwresponse = mwresponse.split()

        if len(magicwords) > 6:
            await cxt.say(":warning: Maximum of 6 magic words allowed in each set.")
            return

        for magicword in magicwords:
            if len(magicword) < 4:
                await cxt.say(":warning: One of the magic words is less than 4 characters, remove or use another")
                return

            if len(magicword) >= 100:
                await cxt.say(":warning: One of the magic words is more than 100 characters, remove or use another")
                return

        if message.server.id not in self.magicwords:
            self.logger.info("New MW Database for %s", message.server.id)
            self.magicwords[message.server.id] = {}

        # check limits
        serverdb = self.magicwords[message.server.id]
        if len(serverdb) >= 10:
            await cxt.say(":elephant: Server reached the limit of 10 Magic Words.")
            return

        # case insensitive
        for i, word in enumerate(magicwords):
            magicwords[i] = word.lower()

        # check duplicates
        for set_id in serverdb:
            mw = serverdb[set_id]
            for word in magicwords:
                if word in mw['words']:
                    await cxt.say(":warning: Conflict: `%s` conflicts with Magic Word Set %d", \
                        (word, set_id))
                    return

        # create mw with new id
        new_id = 1
        # find the first open position for a magic word
        while str(new_id) in serverdb:
            new_id += 1

        self.magicwords[message.server.id][str(new_id)] = {
            'words': magicwords,
            'response': mwresponse
        }

        await cxt.say("M.W. Set %s created!", (new_id,))


    async def c_listmw(self, message, args, cxt):
        '''`j!listmw [set]` - lists available magic words'''

        if message.server.id not in self.magicwords:
            await cxt.say(":warning: Database not created")
            return

        serverdb = self.magicwords[message.server.id]

        if len(args) < 2:
            # list all
            res = []
            for set_id in serverdb:
                mw = serverdb[set_id]
                res.append("%s: %s > %s" % (set_id, mw['words'], mw['response']))

            await cxt.say(self.codeblock("", '\n'.join(res)))
        else:
            set_id = args[1]

            if set_id not in serverdb:
                await cxt.say("Magic Word Set not found")
                return

            mw = serverdb[set_id]
            await cxt.say("`%s: %s > %s`", (set_id, mw['words'], mw['response']))


    async def c_delmw(self, message, args, cxt):
        '''`j!delmw set` - deletes a magic word set'''

        if len(args) < 2:
            await cxt.say(self.c_delmw.__doc__)
            return

        if message.server.id not in self.magicwords:
            await cxt.say(":warning: Database not created")
            return

        set_id = args[1]
        if set_id not in self.magicwords[message.server.id]:
            await cxt.say("Magic Word Set `%r` not found", (set_id,))
            return

        # so it doesn't trigger again
        self.magicwords[message.server.id][set_id] = {
            'words': [str(uuid.uuid4())],
            'response': str(uuid.uuid4()),
        }

        # say to Python to FUCKING DELETE IT
        del self.magicwords[message.server.id][set_id]
        await self.savedb()
        await cxt.say("Deleted set %s", (set_id,))
