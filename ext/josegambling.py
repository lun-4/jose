#!/usr/bin/env python3

import sys
sys.path.append("..")

import discord
import asyncio

import josecommon as jcommon
import joseerror as je
import jcoin.josecoin as jcoin

from random import SystemRandom
random = SystemRandom()

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

    async def c_aposta(self, message, args):
        '''`!aposta` - inicia o modo aposta se ainda não foi ativado'''

        if message.channel.is_private:
            await self.say("Nenhum canal privado é autorizado a iniciar o modo de aposta")
            return

        if not self.gambling_mode:
            self.gambling_mode = True
            await self.say("Modo aposta ativado, mandem seus JC$!")
            return
        else:
            await self.say("Modo aposta já foi ativado :disappointed: ")
            return

    async def c_ap(self, message, args):
        '''`!ap valor` - apostar no sistema de apostas do josé'''

        if len(args) != 2:
            await self.say(self.c_ap.__doc__)
            return

        if not self.gambling_mode:
            await self.say("Modo aposta não foi acionado")
            return

        id_from = message.author.id
        id_to = jcoin.jose_id
        try:
            amount = round(float(args[1]), 3)
        except ValueError:
            await self.say("ValueError: erro parseando o valor")
            return

        fee_amount = amount * (jcommon.GAMBLING_FEE/100.)
        atleast = (amount + fee_amount)

        if amount < self.last_bid:
            await self.say("sua aposta tem que ser maior do que a última, que foi %.2fJC" % self.last_bid)
            return

        a = jcoin.get(id_from)[1]
        if a['amount'] <= atleast:
            await self.say("sua conta não possui fundos suficientes para apostar(%.2fJC são necessários, você tem %.2fJC, faltam %.2fJC)" % (atleast, a['amount'], atleast - a['amount']))
            return

        res = jcoin.transfer(id_from, id_to, atleast, jcoin.LEDGER_PATH)
        await jcoin.raw_save()
        if res[0]:
            await self.say(res[1])
            # use jenv
            if not id_from in self.gambling_env:
                self.gambling_env[id_from] = 0

            self.gambling_env[id_from] += amount
            val = self.gambling_env[id_from]

            self.last_bid = amount
            await self.say("jc_aposta: aposta *total* de %.2f de <@%s>" % (val, id_from))
        else:
            await self.say('jc->error: %s' % res[1])

    async def c_rolar(self, message, args):
        '''`!rolar` - rola e mostra quem é o vencedor'''

        PORCENTAGEM_GANHADOR = 76.54
        PORCENTAGEM_OUTROS = 100 - PORCENTAGEM_GANHADOR

        PORCENTAGEM_GANHADOR /= 100
        PORCENTAGEM_OUTROS /= 100

        K = list(self.gambling_env.keys())
        if len(K) < 2:
            await self.say("Nenhuma aposta com mais de 1 jogador foi feita, modo aposta desativado.")
            self.gambling_mode = False
            return
        winner = random.choice(K)

        M = sum(self.gambling_env.values()) # total
        apostadores = len(self.gambling_env)-1 # remove one because of the winner
        P = (M * PORCENTAGEM_GANHADOR)
        p = (M * PORCENTAGEM_OUTROS) / apostadores

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

        await self.say("%s\nModo aposta desativado!\nhttp://i.imgur.com/huUlJhR.jpg" % (report))

        # clear everything
        self.gambling_env = {}
        self.gambling_mode = False
        self.last_bid = 0.0
        return

    async def c_areport(self, message, args):
        '''`!areport` - relatório da aposta'''
        res = ''
        total = 0.0
        for apostador in self.gambling_env:
            res += '<@%s> apostou %.2fJC\n' % (apostador, self.gambling_env[apostador])
            total += self.gambling_env[apostador]
        res += 'Total apostado: %.2fJC' % (total)

        await self.say(res)

    async def c_acheck(self, message, args):
        '''`!acheck` - mostra se o modo aposta tá ligado ou não'''
        await self.say("Modo aposta: %s" % ["desligado", "ligado"][self.gambling_mode])

    async def c_flip(self, message, args):
        '''`!flip` - joga uma moeda(49%, 49% 2%)'''
        p = random.random()
        if p < 0.49:
            await self.say('http://i.imgur.com/GtTQvaM.jpg') # cara
        elif 0.49 < p < 0.98:
            await self.say("http://i.imgur.com/oPc1siM.jpg") # coroa
        else:
            await self.say("http://i.imgur.com/u4Gem8A.png") # empate
