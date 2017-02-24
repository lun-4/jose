#!/usr/bin/env python3

import asyncio
import sys
sys.path.append("..")
import jauxiliar as jaux
import josecommon as jcommon
import decimal

from random import SystemRandom
random = SystemRandom()

class JoseCoin(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)
        self.counter = 0

    async def ext_load(self):
        return (await self.josecoin_load(None))

    async def ext_unload(self):
        return (await self.josecoin_save(None))

    async def josecoin_save(self, message, dbg_flag=True):
        res = self.jcoin.save('jcoin/josecoin.db')
        if not res[0]:
            if message is not None:
                await self.client.send_message(message.channel, \
                    "jcerr: `%r`" % res)
            else:
                self.logger.error("jcerr: %r" % res)
        return res

    async def josecoin_load(self, message, dbg_flag=True):
        res = self.jcoin.load('jcoin/josecoin.db')
        if not res[0]:
            if message is not None:
                await self.client.send_message(message.channel, \
                    "jcerr: `%r`" % res)
            else:
                self.logger.error("jcerr: %r" % res)
        return res

    async def e_any_message(self, message, cxt):
        self.counter += 1
        if self.counter > 11:
            await self.josecoin_save(message, False)
            self.counter = 0

    async def e_on_message(self, message, cxt):
        if random.random() > jcommon.jc_probabiblity:
            return

        if message.channel.is_private:
            return

        author_id = str(message.author.id)
        if author_id not in self.jcoin.data:
            return

        amount = random.choice(jcommon.JC_REWARDS)
        if amount != 0:
            res = self.jcoin.transfer(self.jcoin.jose_id, author_id, \
                amount, self.jcoin.LEDGER_PATH)

            if res[0]:
                # delay because ratelimits???? need to study that
                await asyncio.sleep(0.5)
                await self.client.add_reaction(message, '💰')
            else:
                jcommon.logger.error("do_josecoin->jc->err: %s", res[1])
                await cxt.say("jc->err: %s", (res[1],))

    async def c_wallet(self, message, args, cxt):
        '''`j!wallet [@mention]` - your wallet(or other person's wallet)'''
        args = message.content.split(' ')

        id_check = None
        if len(args) < 2:
            id_check = message.author.id
        else:
            id_check = await jcommon.parse_id(args[1], message)

        res = self.jcoin.get(id_check)
        if res[0]:
            accdata = res[1]
            await cxt.say(('%s -> %.2f' % (accdata['name'], accdata['amount'])))
        else:
            await cxt.say('account not found(`id:%s`)' % (id_check))

    async def c_account(self, message, args, cxt):
        '''`j!account` - create a new JoséCoin account'''
        self.logger.info("new jc account, id = %s" % message.author.id)

        res = self.jcoin.new_acc(message.author.id, str(message.author))
        if res[0]:
            await cxt.say(res[1])
        else:
            await cxt.say('jc->err: %s' % res[1])

    async def c_write(self, message, args, cxt):
        '''`j!write @mention new_amount` - Overwrite an account's josecoins'''
        global data
        await self.is_admin(message.author.id)

        if len(args) != 3:
            await cxt.say(self.c_write.__doc__)
            return

        try:
            id_from = await jcommon.parse_id(args[1], message)
            new_amount = decimal.Decimal(args[2])
        except Exception as e:
            await cxt.say("huh, exception thingy... `%r`", (e,))
            return

        self.jcoin.data[id_from]['amount'] = new_amount
        await cxt.say("<@%s> has %.2fJC now" % (id_from, \
            self.jcoin.data[id_from]['amount']))

        self.logger.info("%s Wrote %.2fJC to Account %s" % \
            (str(message.author), new_amount, id_from))

    async def c_jcsend(self, message, args, cxt):
        '''`j!jcsend @mention amount` - send JoséCoins to someone'''

        if len(args) != 3:
            await cxt.say(self.c_enviar.__doc__)
            return

        id_to = args[1]
        try:
            amount = decimal.Decimal(args[2])
        except ValueError:
            await cxt.say("ValueError: error parsing value")
            return
        except Exception as e:
            await cxt.say("Exception: `%r`" % e)
            return

        id_from = message.author.id
        id_to = await jcommon.parse_id(id_to, message)

        res = self.jcoin.transfer(id_from, id_to, \
            amount, self.jcoin.LEDGER_PATH)
        await self.josecoin_save(message, False)
        if res[0]:
            await cxt.say(res[1])
        else:
            await cxt.say('jc_err: `%s`' % res[1])

    async def c_ltop10(self, message, args, cxt):
        '''`j!ltop10` - local top 10 people who have high josecoins'''
        if message.server is None:
            await cxt.say("You're not in a server, dummy!")
            return

        guild = message.server
        jcdata = dict(self.jcoin.data) # copy

        range_max = 11 # default 10 users
        if len(args) > 1:
            range_max = int(args[1]) + 1

        if range_max >= 16:
            await cxt.say("LimitError: values higher than 16 aren't valid")
            return
        elif range_max <= 0:
            await cxt.say("haha no")
            return

        maior = {
            'id': 0,
            'name': '',
            'amount': 0.0,
        }

        order = []

        for i in range(1,range_max):
            if len(jcdata) < 1:
                break

            for member in guild.members:
                accid = member.id
                if accid in jcdata:
                    acc = jcdata[accid]
                    name, amount = acc['name'], acc['amount']
                    if amount > maior['amount']:
                        maior['id'] = accid
                        maior['name'] = name
                        maior['amount'] = amount
                else:
                    pass

            if maior['id'] in jcdata:
                del jcdata[maior['id']]
                order.append('%d. %s -> %.2f' % \
                    (i, maior['name'], maior['amount']))

                # reset to next
                maior = {
                    'id': 0,
                    'name': '',
                    'amount': 0.0,
                }

        await cxt.say('\n'.join(order))
        return

    async def c_top10(self, message, args, cxt):
        jcdata = dict(self.jcoin.data) # copy

        range_max = 11 # default 10 users
        if len(args) > 1:
            range_max = int(args[1]) + 1

        maior = {
            'id': 0,
            'name': '',
            'amount': 0.0,
        }

        if range_max >= 16:
            await cxt.say("LimitError: values higher than 16 aren't valid")
            return
        elif range_max <= 0:
            await cxt.say("haha no")
            return

        order = []

        for i in range(1,range_max):
            if len(jcdata) < 1:
                break

            for accid in jcdata:
                acc = jcdata[accid]
                name, amount = acc['name'], acc['amount']
                if amount > maior['amount']:
                    maior['id'] = accid
                    maior['name'] = name
                    maior['amount'] = amount

            del jcdata[maior['id']]
            order.append('%d. %s -> %.2f' % \
                (i, maior['name'], maior['amount']))

            # reset to next
            maior = {
                'id': 0,
                'name': '',
                'amount': 0.0,
            }

        await cxt.say('\n'.join(order))
        return
