#!/usr/bin/env python3

import discord
import asyncio
import sys
import os
import json

sys.path.append("..")
import jauxiliar as jaux
import joseerror as je
import joseconfig as jconfig

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
        else:
            res.append(char)
        i += 1

    return ''.join(res)

async def mw_response(mw, message):
    return parse(mw['response'], message)

async def mw_match(mw, string):
    for word in mw['words']:
        if word == string:
            return True

class JoseMagicWord(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)
        self.db_magicword_path = jconfig.MAGICWORD_PATH
        self.magicwords = {}
        self.counter = 0

    async def savedb(self):
        self.logger.info("Saving Magicword database")
        json.dump(self.magicwords, open(self.db_magicword_path, 'w'))

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

    async def e_any_message(self, message):
        if self.counter % 25 == 0:
            await self.savedb()

        if message.server.id in self.magicwords:
            mwsdb = self.magicwords[message.server.id]
            print(mwsdb)
            for set_id in mwsdb:
                mw = mwsdb[set_id]
                print(mw)
                if mw_match(mw, message.content):
                    await self.say(mw_response(mw, message))

        self.counter += 1

    async def c_setmw(self, message, args):
        '''`!setmw magicword1,magicword2,magicword3;response` - Magic Words
        docs: https://github.com/lkmnds/jose/blob/master/doc/magicwords.md'''

        if len(args) < 2:
            await self.say(self.c_setmagic.__doc__)
            return

        # get string that represents the magic word
        mwstr = ' '.join(args[1:])

        if ';' not in mwstr:
            await self.say("Malformed string")
            return

        # parse the string
        magicwords, mwresponse = mwstr.split(';')
        magicwords = magicwords.split(',')

        if len(magicwords) > 5:
            await self.say(":warning: Maximum of 4 magic words allowed in each set.")
            return

        if message.server.id not in self.magicwords:
            self.logger.info("New MW Database for %s", message.sever.id)
            self.magicwords[message.server.id] = {}

        # check duplicates
        serverdb = self.magicwords[message.server.id]
        for set_id in serverdb:
            mw = serverdb[mword_id]
            for word in magicwords:
                if word in mw['words']:
                    await self.say(":warning: Conflict: `%s` conflicts with Magic Word Set %d" % \
                        (word, set_id))
                    return

        # create mw with new id
        new_id = str(len(serverdb) + 1)
        serverdb[new_id] = {
            'words': magicwords,
            'response': mwresponse
        }

        await self.say("M.W. Set %s created!" % new_id)


    async def c_listmw(self, message, args):
        '''`!listmw [set]` - lists available magic words'''

        if message.server.id not in self.magicwords:
            await self.say(":warning: Database not created")
            return

        serverdb = self.magicwords[message.server.id]

        if len(args) < 2:
            # list all
            res = []
            for set_id in serverdb:
                mw = serverdb[set_id]
                res.append("%s: %s > %s" % (set_id, mw['words'], mw['response']))

            await self.say(self.codeblock("", ''.join(res)))
        else:
            set_id = args[1]

            if set_id not in serverdb:
                await self.say("Magic Word Set not found")
                return

            mw = serverdb[set_id]
            await self.say("`%s: %s > %s`" % (set_id, mw['words'], mw['response']))


    async def c_delmw(self, message, args):
        '''`!delmw set` - deletes a magic word set'''

        if len(args) < 2:
            await self.say(self.c_delmagic.__doc__)
            return

        if message.server.id not in self.magicwords:
            await self.say(":warning: Database not created")
            return

        serverdb = self.magicwords[message.server.id]

        set_id = args[1]

        if set_id not in serverdb:
            await self.say("Magic Word Set not found")
            return

        del serverdb[set_id]
        await self.say("Deleted set %s" % set_id)
