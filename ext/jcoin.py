#!/usr/bin/env python3

import asyncio
import sys
sys.path.append("..")
import jauxiliar as jaux
import josecommon as jcommon
import decimal
import json
import os
import time

from random import SystemRandom
random = SystemRandom()

PRICE_TABLE = {
    'api': ('Tax for Commands that use APIs', jcommon.API_TAX_PRICE, \
            ('wolframalpha', 'temperature', 'money', 'bitcoin', '8ball', \
                'xkcd', 'sndc')),

    'img': ('Price for all commands in `joseimages`', jcommon.IMG_PRICE, \
            ('derpibooru', 'hypno', 'e621', 'yandere')),

    'opr': ('Operational tax for commands that use a lot of processing', jcommon.OP_TAX_PRICE, \
            ('datamosh', 'yt'))
}

# 1%
BASE_CHANCE = 1
STEALDB_PATH = 'db/steal.json'

DEFAULT_STEALDB = '''{
    "points": {},
    "cdown": {},
    "period": {}
}'''

HELPTEXT_JC_STEAL = """
`j!steal` allows you to steal an arbritary amount of money from anyone.
use `j!stealstat` to see your status in the stealing business.

The chance of getting caught increases faster than the amount you want to steal
"""

class JoseCoin(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)
        self.counter = 0

    async def josecoin_save(self, message, dbg_flag=True):
        res = self.jcoin.save('jcoin/josecoin.db')
        if not res[0]:
            self.logger.error("jcerr: %r", res)
            if message is not None:
                await self.client.send_message(message.channel, \
                    "jcerr: `%r`" % res)
        return res

    async def josecoin_load(self, message, dbg_flag=True):
        res = self.jcoin.load('jcoin/josecoin.db')
        if not res[0]:
            self.logger.error("jcerr: %r", res)
            if message is not None:
                await self.client.send_message(message.channel, \
                    "jcerr: `%r`" % res)
        return res

    async def save_steal_db(self):
        try:
            self.logger.info("savedb:stealdb")
            json.dump(self.stealdb, open(STEALDB_PATH, 'w'))

            return True, ''
        except Exception as err:
            return False, str(err)

    async def load_steal_db(self):
        try:
            self.stealdb = {}
            if not os.path.isfile(STEALDB_PATH):
                with open(STEALDB_PATH, 'w') as stealdbfile:
                    stealdbfile.write(DEFAULT_STEALDB)

            self.stealdb = json.load(open(STEALDB_PATH, 'r'))

            return True, ''
        except Exception as err:
            return False, str(err)

    async def ext_load(self):
        res_jc = await self.josecoin_load(None)
        if not res_jc[0]:
            return res_jc

        res_sdb = await self.load_steal_db()
        if not res_sdb[0]:
            return res_sdb

        return True, ''

    async def ext_unload(self):
        res_jc = await self.josecoin_load(None)
        if not res_jc[0]:
            return res_jc

        res_sdb = await self.save_steal_db()
        if not res_sdb[0]:
            return res_sdb

        return True, ''

    async def e_any_message(self, message, cxt):
        self.counter += 1
        if self.counter > 11:
            await self.josecoin_save(message, False)
            self.counter = 0

    async def e_on_message(self, message, cxt):
        if random.random() > jcommon.JC_PROBABILITY:
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

    async def c_prices(self, message, args, cxt):
        '''`j!prices` - show price categories'''
        res = []

        for cat in sorted(PRICE_TABLE):
            data = PRICE_TABLE[cat]
            desc = data[0]
            price = data[1]
            commands = data[2]

            _cmdlist = ['j!{}'.format(cmd) for cmd in commands]
            cmdlist = ', '.join(_cmdlist)

            res.append("`%s`: %.2fJC, *%s*, `%s`" % (cat, price, desc, cmdlist))

        await cxt.say('\n'.join(res))

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

    async def c_balance(self, message, args, cxt):
        '''`j!balance [@mention]` - alias to `j!wallet`'''
        await self.c_wallet(message, args, cxt)

    async def c_bal(self, message, args, cxt):
        '''`j!balance [@mention]` - alias to `j!wallet`'''
        await self.c_wallet(message, args, cxt)

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
            await cxt.say(self.c_jcsend.__doc__)
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

    async def c_hsteal(self, message, args, cxt):
        await cxt.say(HELPTEXT_JC_STEAL)

    async def c_stealstat(self, message, args, cxt):
        # get status from person
        personid = message.author.id

        res = []

        points = self.stealdb['points'].get(personid, 3)
        prison = self.stealdb['cdown'].get(personid, None)
        grace_period = self.stealdb['period'].get(personid, None)

        res.append("**%s**, you have %d stealing points", str(message.author), points)
        if prison is not None:
            res.append(":cop: you're in prison, %d seconds remaining", prison)

        if grace_period is not None:
            res.append(":angel: you're in grace period, %d seconds remaining", grace_period)

        await cxt.say('\n'.join(res))

    async def c_steal(self, message, args, cxt):
        '''`j!steal @target amount` - Steal JoséCoins from someone'''

        if len(args) < 2:
            await cxt.say(self.c_steal.__doc__)
            return

        # parse mention
        try:
            target_id = await jcommon.parse_id(args[1])
        except:
            await cxt.say("Error parsing `@target`")
            return

        try:
            amount = decimal.Decimal(args[2])
        except:
            await cxt.say("Error parsing `amount`")
            return

        if message.author.id not in self.jcoin.data:
            await cxt.say("You don't have a josécoin account.")
            return

        if target_id not in self.jcoin.data:
            await cxt.say("The person you're trying to steal from doesn't have a JoséCoin account")
            return

        thief_id = message.author.id

        # check if thief has cooldowns in place
        cdown = self.stealdb['cdown'].get(thief_id, None)
        if cdown is not None:
            cooldown_end, cooldown_type = cdown
            remaining = cooldown_end - time.time()
            if cooldown_type == 0:
                await cxt.say(":cop: You are still in prison, wait %d seconds", (remaining,))
            elif cooldown_type == 1:
                if remaining > 1:
                    await cxt.say("Wait %d seconds to regenerate your stealing points", (remaining,))
                else:
                    await cxt.say("Stealing points regenerated!")
                    del self.stealdb['points'][thief_id]
                    await self.save_steal_db()
            return

        stealuses = self.stealdb['points'].get(thief_id, None)
        if stealuses is None:
            self.stealdb['points'][thief_id] = stealuses = 3

        thief_user = await self.client.get_user_info(thief_id)

        grace_period = (time.time() - self.stealdb['period'].get(target_id, 0))
        if grace_period > 0:
            await cxt.say("Target is in :angel: grace period :grace:")
            await cxt.say("%s tried to steal %.2fJC from you, but you have %d seconds of grace period", \
                (str(thief_user), amount, grace_period))
            return

        if stealuses < 1:
            await cxt.say("You don't have any more stealing points, wait 24 hours to get more.")
            self.stealdb['cdown'][thief_id] = (time.time() + 86400, 1)
            return

        if target_id == self.jcoin.jose_id:
            await cxt.say(":cop: You can't steal from José. Arrested for 24h")
            self.stealdb['cdown'][thief_id] = (time.time() + 86400, 0)
            return

        target_account = self.jcoin.get(target_id)
        target_amount = target_account['amount']

        if amount > target_amount:
            # automatically in prison
            await cxt.say(":cop: Arrested because you tried to steal more than the target has, got 24h jailtime.")
            self.stealdb['cdown'][thief_id] = (time.time() + 86400, 0)

        chance = (BASE_CHANCE + (target_amount / amount)) * 0.3
        res = random.random() * 100

        if res < chance:
            self.logger.info("Stealing %.2fJC from %s[%s] to %s[%s]", \
                amount, target_account['name'], target_id, message.author, thief_id)

            # steal went good, make transfer
            ok = self.jcoin.transfer(target_id, thief_id, amount)

            # check transfer status
            if not ok[0]:
                await cxt.say("jc->err: %s", ok[1])
            else:
                await cxt.say("Good one! Stealing went well, nobody noticed, you thief. Got %.2fJC from %s, \n`%s`", \
                    (amount, target_account['name'], ok[1]))

                target_user = await self.client.get_user_info(target_id)
                await cxt.say(":gun: You got robbed! The thief(%s) stole `%.2fJC` from you. 2 hour grace period", \
                    (str(thief_user), amount), target_user)

                self.stealdb['period'][target_id] = time.time() + 10800
                self.stealdb['points'][message.author.id] -= 1

        else:
            # type 0 cooldown, you got arrested
            await cxt.say(":cop: Arrested! got 24h cooldown on `j!steal`.")
            self.stealdb['cdown'][message.author.id] = (time.time() + 86400, 0)

        await self.save_steal_db()

    async def c_roubar(self, message, args, cxt):
        '''`j!roubar @target amount` - alias for `j!steal`'''
        await self.c_steal(message, args, cxt)
