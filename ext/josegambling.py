#!/usr/bin/env python3

import decimal
from random import SystemRandom
random = SystemRandom()

import sys
sys.path.append("..")
import jauxiliar as jaux

BETTING_FEE = 5
PERCENTAGE_WIN = 100

class JoseGambling(jcommon.Extension):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)
        self.sessions = {}

    async def ext_load(self):
        return True, ''

    async def ext_unload(self):
        return True, ''

    async def empty_session(self):
        return {
            'betters': {},
            'last_bet': 0.0,
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

        session = self.sesisons[message.server.id]

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
            await cxt.say("Your bet needs to be higher than %.2fJC", (self.last_bid,))
            return

        fee_amount = decimal.Decimal(amount) * decimal.Decimal(BETTING_FEE/100.)
        atleast = (decimal.Decimal(amount) + fee_amount)

        a = self.jcoin.get(id_from)[1]
        if a['amount'] <= atleast:
            await cxt.say("No sufficient funds(need %.2fJC in total, you have %.2fJC, needs %.2fJC)", \
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

            await cxt.say("jcroulette: Total bet of %.2fJC from <@%s>\nJC report: %s", \
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

        PERCENTAGE_WIN = 76.54
        PERCENTAGE_OTHERS = 100 - PERCENTAGE_WIN

        PERCENTAGE_WIN /= 100
        PERCENTAGE_OTHERS /= 100

        session = self.sesison[message.server.id]
        betters = session['betters']

        K = list(betters.keys())
        if len(K) < 2:
            await cxt.say("Session without 2 or more players, closing down.")
            del self.session[message.server.id], session
            return

        winner = random.choice(K)

        M = sum(betters.values(), decimal.Decimal(0)) # total
        len_betters = len(betters) - 1 # remove one because of the winner
        P = (M * decimal.Decimal(PERCENTAGE_WIN))
        p = (M * decimal.Decimal(PERCENTAGE_OTHERS)) / decimal.Decimal(len_betters)

        if self.jcoin.data[self.jcoin.jose_id]['amount'] < M:
            await self.debug("aposta->jc: **THIS IS BAD, JOSÉ DOESNT HAVE ENOUGH FUNDS FOR TRANSACTION**")

        report = ''

        res = self.jcoin.transfer(self.jcoin.jose_id, winner, P, self.jcoin.LEDGER_PATH)
        if res[0]:
            report += "**WINNER:** <@%s> won %.2fJC!\n" % (winner, P)
        else:
            await self.debug("jc_jcroulette->jc: %s\naborting jr mode" % res[1])
            return

        del self.session[message.server.id]['betters'][winner]
        del session['betters'][winner]
        del betters[winner]

        # going well...
        for bet_user in betters:
            res = self.jcoin.transfer(self.jcoin.jose_id, apostador, p, self.jcoin.LEDGER_PATH)
            if res[0]:
                report += "<@%s> won %.2fJC!\n" % (apostador, p)
            else:
                await self.debug("jc_aposta->self.jcoin: %s" % res[1])
                return

        # http://i.imgur.com/huUlJhR.jpg
        await cxt.say("%s\nJC roulette is off!\n", (report,))

        del del self.session[message.server.id], session, betters
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

        res = ''
        total = decimal.Decimal(0)
        for apostador in session['betters']:
            res += '<@%s> bet %.2fJC\n' % (apostador, self.gambling_env[apostador])
            total += decimal.Decimal(self.gambling_env[apostador])
        res += 'Total of %.2fJC' % (total)

        await cxt.say(res)

    async def c_jrcheck(self, message, args, cxt):
        '''`j!jrcheck` - mostra se o modo aposta tá ligado ou não'''
        if message.channel.is_private:
            await cxt.say("DMs can't use JC Roulette")
            return

        session = self.session.get(message.server.id, False)
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

    async def c_adummy(self, message, args, cxt):
        await cxt.say(jcommon.GAMBLING_HELP_TEXT_SMALL)

    async def c_ahelp(self, message, args, cxt):
        await cxt.say(jcommon.GAMBLING_HELP_TEXT)
