#!/usr/bin/env python3

import decimal
import sys
from random import SystemRandom
random = SystemRandom()

sys.path.append("..")
import josecommon as jcommon
import joseerror as je
import jcoin.josecoin as jcoin

class JoseGambling(jcommon.Extension):
    def __init__(self, cl):
        jcommon.Extension.__init__(self, cl)
        self.last_bid = 0.0
        self.gambling_mode = False
        self.gambling_env = {}

    async def ext_load(self):
        self.last_bid = 0.0
        self.gambling_mode = False
        self.gambling_env = {}
        return True, ''

    async def c_aposta(self, message, args, cxt):
        '''`!aposta` - inicia o modo aposta se ainda não foi ativado'''

        if message.channel.is_private:
            await cxt.say("Nenhum canal privado é autorizado a iniciar o modo de aposta")
            return

        if not self.gambling_mode:
            self.gambling_mode = True
            await cxt.say("Modo aposta ativado, mandem seus JC$!")
            return
        else:
            await cxt.say("Modo aposta já foi ativado :disappointed: ")
            return

    async def c_ap(self, message, args, cxt):
        '''`!ap valor` - apostar no sistema de apostas do josé'''

        if len(args) != 2:
            await cxt.say(self.c_ap.__doc__)
            return

        if not self.gambling_mode:
            await cxt.say("Modo aposta não foi acionado")
            return

        id_from = message.author.id
        id_to = jcoin.jose_id
        amount = decimal.Decimal(0)
        try:
            if args[1] == 'all':
                from_amnt = jcoin.get(id_from)[1]['amount'] - 0.1
                fee_amnt = from_amnt * decimal.Decimal(jcommon.GAMBLING_FEE/100.)
                amount = from_amnt - fee_amnt
            else:
                amount = round(float(args[1]), 3)
        except ValueError:
            await cxt.say("ValueError: erro parseando o valor")
            return

        fee_amount = decimal.Decimal(amount) * decimal.Decimal(jcommon.GAMBLING_FEE/100.)
        atleast = (decimal.Decimal(amount) + fee_amount)

        if amount < self.last_bid:
            await cxt.say("sua aposta tem que ser maior do que a última, que foi %.2fJC" % self.last_bid)
            return

        a = jcoin.get(id_from)[1]
        if a['amount'] <= atleast:
            await cxt.say("sua conta não possui fundos suficientes para apostar(%.2fJC são necessários, você tem %.2fJC, faltam %.2fJC)" % \
                (atleast, a['amount'], decimal.Decimal(atleast) - a['amount']))
            return

        res = jcoin.transfer(id_from, id_to, atleast, jcoin.LEDGER_PATH)
        await jcoin.raw_save()
        if res[0]:
            await cxt.say(res[1])
            # use jenv
            if id_from not in self.gambling_env:
                self.gambling_env[id_from] = decimal.Decimal(0)

            self.gambling_env[id_from] += decimal.Decimal(amount)
            val = self.gambling_env[id_from]

            self.last_bid = amount
            await cxt.say("jc_aposta: aposta *total* de %.2f de <@%s>" % (val, id_from))
        else:
            await cxt.say('jc->error: %s' % res[1])

    async def c_rolar(self, message, args, cxt):
        '''`!rolar` - rola e mostra quem é o vencedor'''

        PORCENTAGEM_GANHADOR = 76.54
        PORCENTAGEM_OUTROS = 100 - PORCENTAGEM_GANHADOR

        PORCENTAGEM_GANHADOR /= 100
        PORCENTAGEM_OUTROS /= 100

        K = list(self.gambling_env.keys())
        if len(K) < 2:
            await cxt.say("Nenhuma aposta com mais de 1 jogador foi feita, modo aposta desativado.")
            self.gambling_mode = False
            return
        winner = random.choice(K)

        M = sum(self.gambling_env.values(), decimal.Decimal(0)) # total
        apostadores = len(self.gambling_env)-1 # remove one because of the winner
        P = (M * decimal.Decimal(PORCENTAGEM_GANHADOR))
        p = (M * decimal.Decimal(PORCENTAGEM_OUTROS)) / decimal.Decimal(apostadores)

        if jcoin.data[jcoin.jose_id]['amount'] < M:
            await self.debug("aposta->jc: **JOSÉ NÃO POSSUI FUNDOS SUFICIENTES PARA A APOSTA**")

        report = ''

        res = jcoin.transfer(jcoin.jose_id, winner, P, jcoin.LEDGER_PATH)
        if res[0]:
            report += "**GANHADOR:** <@%s> ganhou %.2fJC!\n" % (winner, P)
        else:
            await self.debug("jc_gambling->jc: %s\naposta abortada" % res[1])
            return

        del self.gambling_env[winner]

        # going well...
        for apostador in self.gambling_env:
            res = jcoin.transfer(jcoin.jose_id, apostador, p, jcoin.LEDGER_PATH)
            if res[0]:
                report += "<@%s> ganhou %.2fJC nessa aposta!\n" % (apostador, p)
            else:
                await self.debug("jc_aposta->jcoin: %s" % res[1])
                return

        await cxt.say("%s\nModo aposta desativado!\nhttp://i.imgur.com/huUlJhR.jpg" % (report))

        # clear everything
        self.gambling_env = {}
        self.gambling_mode = False
        self.last_bid = 0.0
        return

    async def c_areport(self, message, args, cxt):
        '''`!areport` - relatório da aposta'''
        res = ''
        total = decimal.Decimal(0)
        for apostador in self.gambling_env:
            res += '<@%s> apostou %.2fJC\n' % (apostador, self.gambling_env[apostador])
            total += decimal.Decimal(self.gambling_env[apostador])
        res += 'Total apostado: %.2fJC' % (total)

        await cxt.say(res)

    async def c_acheck(self, message, args, cxt):
        '''`!acheck` - mostra se o modo aposta tá ligado ou não'''
        await cxt.say("Modo aposta: %s" % ["desligado", "ligado"][self.gambling_mode])

    async def c_flip(self, message, args, cxt):
        '''`!flip` - joga uma moeda(49%, 49% 2%)'''
        p = random.random()
        if p < 0.49:
            await cxt.say('http://i.imgur.com/GtTQvaM.jpg') # cara
        elif 0.49 < p < 0.98:
            await cxt.say("http://i.imgur.com/oPc1siM.jpg") # coroa
        else:
            await cxt.say("http://i.imgur.com/u4Gem8A.png") # empate
