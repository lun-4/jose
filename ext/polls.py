#!/usr/bin/env python3

import sys
sys.path.append("..")
import jauxiliar as jaux
import joseerror as je

class Polls(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)

        self.jsondb('polls', path='db/polls.json')

    async def ext_load(self):
        try:
            return True, ''
        except Exception as err:
            return False, repr(err)

    async def ext_unload(self):
        try:
            return True, ''
        except Exception as err:
            return False, repr(err)

    async def c_mkpoll(self, message, args, cxt):
        '''`j!mkpoll title;op1;op2;...;opN` - create a poll'''

        # parse shit
        try:
            s = ' '.join(args[1:])
            sp = s.split(';')
            title = sp[0]
            options = sp[1:]
        except:
            await cxt.say("Error parsing your shit!!!!!")
            return

        await cxt.say("`%r %r`", (title, options))
