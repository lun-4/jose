#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import jauxiliar as jaux
import joseerror as je

class JoseCoin(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)
        self.top10_flag = False
        self.data = self.jcoin.data

    async def josecoin_save(self, message, dbg_flag=True):
        res = self.jcoin.save('jcoin/josecoin.db')
        if not res[0]:
            await self.client.send_message(message.channel, "jcerr: `%r`" % res)

    async def josecoin_load(self, message, dbg_flag=True):
        res = self.jcoin.load('jcoin/josecoin.db')
        if not res[0]:
            await self.client.send_message(message.channel, "jcerr: `%r`" % res)

    async def c_saldo(self, message, args, cxt):
        '''`j!saldo [@mention]` - your wallet(or other person's wallet)'''
        args = message.content.split(' ')

        id_check = None
        if len(args) < 2:
            id_check = message.author.id
        else:
            id_check = await jcommon.parse_id(args[1], message)

        res = get(id_check)
        if res[0]:
            accdata = res[1]
            await cxt.say(('%s -> %.2f' % \
                (accself.data['name'], accself.data['amount'])))
        else:
            await cxt.say('account not found(`id:%s`)' % (id_check))

    async def c_conta(self, message, args, cxt):
        '''`j!conta` - create a new JoséCoin account'''
        self.logger.info("new jc account, id = %s" % message.author.id)

        res = new_acc(message.author.id, str(message.author))
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

        self.data[id_from]['amount'] = new_amount
        await cxt.say("<@%s> has %.2fJC now" % (id_from, \
            self.data[id_from]['amount']))

        self.logger.info("%r Wrote %.2fJC to Account %s" % \
            (message.author, new_amount, id_from))

    async def c_enviar(self, message, args, cxt):
        '''`j!enviar @mention quantidade` - envia JCoins para uma conta'''

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

        res = transfer(id_from, id_to, amount, LEDGER_PATH)
        await self.josecoin_save(message, False)
        if res[0]:
            await cxt.say(res[1])
        else:
            await cxt.say('jc_err: `%s`' % res[1])

    async def c_ltop10(self, message, args, cxt):
        guild = message.server
        jcdata = dict(data) # copy

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
                    acc = jcself.data[accid]
                    name, amount = acc['name'], acc['amount']
                    if amount > maior['amount']:
                        maior['id'] = accid
                        maior['name'] = name
                        maior['amount'] = amount
                else:
                    pass

            if maior['id'] in jcdata:
                del jcself.data[maior['id']]
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
        jcdata = dict(data) # copy

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
                acc = jcself.data[accid]
                name, amount = acc['name'], acc['amount']
                if amount > maior['amount']:
                    maior['id'] = accid
                    maior['name'] = name
                    maior['amount'] = amount

            del jcself.data[maior['id']]
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
