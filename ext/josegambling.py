#!/usr/bin/env python3

import decimal
from random import SystemRandom
random = SystemRandom()

import sys
sys.path.append("..")
import jauxiliar as jaux

BETTING_FEE = 5

JCROULETTE_HELP_TEXT = '''
JoséCoin Roulette, abbreviated as JC Roulette, is a form of russian roulette
where people create a JCR session, they pay josé, and josé chooses, by random,
a winner that will win all the money everyone paid.

`j!jrstart` to start a session
`j!jrbet` to pay josé, 5%% of this amount will be fees
`j!jrdo` does the roulette, when everyone wants to know who wins
`j!jreport` shows if JCR is on or off in your server
'''

class JoseGambling(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)
        self.sessions = {}

    async def ext_load(self):
        return True, ''

    async def ext_unload(self):
        return True, ''

    async def empty_session(self):
        return {
            'betters': {},
            'last_bid': 0.0,
        }

    async def c_jrstart(self, message, args, cxt):
        '''`j!jrstart` - Start JC Roulette in this server'''
        if message.channel.is_private:
            await cxt.say("DMs can't use JC Roulette")
            return

        if message.server.id in self.sessions:
            await cxt.say("Session already exists :disappointed:")
            return

        self.sessions[message.server.id] = await self.empty_session()
        await cxt.say("Session created!")

    async def c_jrbet(self, message, args, cxt):
        '''`j!jrbet value` bet in JoséCoin Roulette :tm:'''

        if message.channel.is_private:
            await cxt.say("DMs can't use JC Roulette")
            return

        if message.server.id not in self.sessions:
            await cxt.say("No session found for this server, use `j!jrstart`")
            return

        if len(args) != 2:
            await cxt.say(self.c_jrbet.__doc__)
            return

        session = self.sessions[message.server.id]

        id_from = message.author.id
        id_to = self.jcoin.jose_id
        amount = None
        try:
            if args[1] == 'all':
                from_amnt = self.jcoin.get(id_from)[1]['amount'] - 0.1
                fee_amnt = from_amnt * decimal.Decimal(BETTING_FEE/100.)
                amount = from_amnt - fee_amnt
            else:
                amount = round(float(args[1]), 2)
        except ValueError:
            await cxt.say("Error parsing value")
            return

        if amount < session['last_bid']:
            await cxt.say("Your bet needs to be higher than `%.2fJC`", (self.last_bid,))
            return

        fee_amount = decimal.Decimal(amount) * decimal.Decimal(BETTING_FEE/100.)
        atleast = (decimal.Decimal(amount) + fee_amount)

        a = self.jcoin.get(id_from)[1]
        if a['amount'] <= atleast:
            await cxt.say("No sufficient funds(need `%.2fJC` in total, you have `%.2fJC`, needs `%.2fJC`)", \
                (atleast, a['amount'], decimal.Decimal(atleast) - a['amount']))
            return

        res = self.jcoin.transfer(id_from, id_to, atleast)
        await self.jcoin.raw_save()

        if res[0]:
            if id_from not in session['betters']:
                session['betters'][id_from] = decimal.Decimal(0)

            session['betters'][id_from] += decimal.Decimal(amount)
            val = session['betters'][id_from]
            session['last_bid'] = amount

            await cxt.say("jcroulette: Total bet of `%.2fJC` from <@%s>\nJC report: %s", \
                (val, id_from, res[1]))
        else:
            await cxt.say('jc->err: %s', (res[1],))

    async def c_jrdo(self, message, args, cxt):
        '''`j!jrdo` - Does the JoséCoin Roulette :tm:'''

        if message.channel.is_private:
            await cxt.say("DMs can't use JC Roulette")
            return

        if message.server.id not in self.sessions:
            await cxt.say("No session found for this server, use `j!jrstart`")
            return

        session = self.sesisons[message.server.id]
        betters = session['betters']

        K = list(betters.keys())
        if len(K) < 2:
            await cxt.say("Session without 2 or more players, closing session.")
            del self.sessions[message.server.id], session, betters
            return

        winner = random.choice(K)

        # total stuff
        total_amount = sum(betters.values(), decimal.Decimal(0))

        if self.jcoin.data[self.jcoin.jose_id]['amount'] < total_amount:
            await cxt.err("jc->check: **THIS IS BAD, JOSÉ DOESNT HAVE ENOUGH FUNDS FOR TRANSACTION**")

        report = ''

        res = self.jcoin.transfer(self.jcoin.jose_id, winner, total_amount)
        if res[0]:
            report += "**WINNER:** <@%s> won `%.2fJC`!\n" % (winner, total_amount)
        else:
            await self.debug("jc_jcroulette->jc: %s\naborting jr mode" % res[1])
            del self.sessions[message.server.id], session, betters
            return

        # http://i.imgur.com/huUlJhR.jpg
        await cxt.say("%s\nJC roulette is off!\n", (report,))

        del self.sessions[message.server.id], session, betters
        return

    async def c_jreport(self, message, args, cxt):
        '''`j!jreport` - JC Roulette report'''
        if message.channel.is_private:
            await cxt.say("DMs can't use JC Roulette")
            return

        if message.server.id not in self.sessions:
            await cxt.say("No session found for this server, use `j!jrstart`")
            return

        session = self.sessions[message.server.id]

        res = []
        total = decimal.Decimal(0)
        for userid in session['betters']:
            val = session['betters'][userid]
            res.append('<@%s> used `%.2fJC`' % (userid, val))
            total += decimal.Decimal(val)

        res.append('Total of `%.2fJC`' % (total))
        await cxt.say('\n'.join(res))

    async def c_jrcheck(self, message, args, cxt):
        '''`j!jrcheck` - shows if jcroulette is on or not'''
        if message.channel.is_private:
            await cxt.say("DMs can't use JC Roulette")
            return

        session = self.sessions.get(message.server.id, False)
        await cxt.say("JC Roulette: %s", (["off", "on"][session],))

    async def c_flip(self, message, args, cxt):
        '''`j!flip` - joga uma moeda(49%, 49% 2%)'''
        p = random.random()
        if p < 0.49:
            await cxt.say('http://i.imgur.com/GtTQvaM.jpg') # cara
        elif 0.49 < p < 0.98:
            await cxt.say("http://i.imgur.com/oPc1siM.jpg") # coroa
        else:
            await cxt.say("http://i.imgur.com/u4Gem8A.png") # empate

    async def c_jcrhelp(self, message, args, cxt):
        await cxt.say(JCROULETTE_HELP_TEXT)
