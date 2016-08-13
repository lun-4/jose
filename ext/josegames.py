#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import josecommon as jcommon
import joseerror as je

import pickle
from random import SystemRandom
random = SystemRandom()

import random as normal_random
from itertools import combinations

NORMAL_CP = 50

'''
    bad CP => 100
    good CP => 600+
'''

dgo_data = {
    1: ['Deus',     (NORMAL_CP      , 600)],
    2: ['Belzebu',  (NORMAL_CP      , 500)],
    3: ['Zeus',     (NORMAL_CP      , 450)],
    4: ['Thor',     (NORMAL_CP      , 500)],
    5: ['Apolo',    (NORMAL_CP      , 500)],
    6: ['Hélio',    (NORMAL_CP      , 500)],
    7: ['Hércules', (NORMAL_CP      , 500)],
    8: ['Dionísio', (NORMAL_CP - 200, 500)],
    9: ['Hades',    (NORMAL_CP      , 400)],
}

items = {
    0: "Hóstias",
    1: "Poção",
    2: "Incenso",
    3: "Doces",
}

RARE_PROB = 0.01
RARE_DEUSES = list(range(4))

COMMON_PROB = 0.1
COMMON_DEUSES = list(range(5,9+1))

class Item(object):
    def __init__(self, itemid):
        self.id = itemid
        self.name = items[itemid]
    def __str__(self):
        return self.name


async def calc_iv(cp, pr):
    # calculate [ATK, DEF, STA]
    base = cp * (pr * (cp / 3))
    normal_random.seed(base)
    c = list(combinations(range(15),3))
    for el in c:
        for n in c:
            if n < 6:
                del el
    return normal_random.choice(c)

async def create_deusmon(did):
    d = Deusmon(did)
    d.iv = await calc_iv(d.combat_power, d.data[1])
    return d

class Deusmon:
    def __init__(self, did):
        self.id = did
        self.data = dgo_data[did]
        self.name = data[0]

        self.combat_power = random.randint(self.data[2][0], self.data[2][1])

def make_encounter():
    did = 0
    p = random.random()
    if p < RARE_PROB:
        did = random.choice(RARE_DEUSES)
    elif p < COMMON_PROB:
        did = random.choice(COMMON_DEUSES)
    else:
        return None

    d = Deusmon(random.randint())
    return d

class JoseGames(jcommon.Extension):
    def __init__(self, cl):
        jcommon.Extension.__init__(self, cl)
        self.db = {}

    async def ext_load(self):
        try:
            self.db = pickle.load(open('d-go.db', 'rb'))
            return True
        except Exception as e:
            return False, repr(e)

    async def ext_unload(self):
        try:
            pickle.dump(self.db, open('d-go.db', 'wb'))
            return True
        except Exception as e:
            return False, repr(e)

    async def c_dgoinit(self, message, args):
        '''`!dgoinit` - inicia uma conta no Deusesmon GO'''
        self.db[message.author.id] = {
            'coin': 0,
            'xp': 0,
            'level': 1,
            'inv': [
                (50, Item(0)), # 50 Balls
                (5, Item(1)), # 5 Potions
                (1, Item(2)), # 1 Incense
                (10, Item(3)), # 10 Berry
            ],
            'dinv': {},
        }
        await self.say("conta criada para <@%s>!" % message.author.id)

    async def c_dgosave(self, message, args):
        done = await self.ext_unload()
        if done:
            await self.say("salvo.")
        elif not done[0]:
            await self.say("py_err: %s" % done[1])
        return

    async def c_dgoload(self, message, args):
        done = await self.ext_load()
        if done:
            await self.say("carregado.")
        elif not done[0]:
            await self.say("py_err: %s" % done[1])
        return

    async def c_dgostat(self, message, args):
        '''`!dgostat` - mostra os status do seu personagem'''
        player_data = self.db[message.author.id]

        res = ''
        res += '%s\n' % message.author
        res += 'Inventário:\n'
        for el in player_data['inv']:
            res += '\t\t%d %s' % (el[0], str(el[1]))

        res = '```%s```' % res
        await self.say(res)
