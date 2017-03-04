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
                'xkcd', 'sndc', 'urban')),

    'img': ('Price for all commands in `joseimages`', jcommon.IMG_PRICE, \
            ('derpibooru', 'hypno', 'e621', 'yandere')),

    'opr': ('Operational tax for commands that use a lot of processing', jcommon.OP_TAX_PRICE, \
            ('datamosh', 'yt'))
}

# 1%
BASE_CHANCE = decimal.Decimal(1)
STEALDB_PATH = 'db/steal.json'
ARREST_TIME = 28800 # 8 hours

DEFAULT_STEALDB = '''{
    "points": {},
    "cdown": {},
    "period": {}
}'''

HELPTEXT_JC_STEAL = """
`j!steal` allows you to steal an arbritary amount of money from anyone.
use `j!stealstat` to see your status in the stealing business.

The chance of getting caught increases the more you steal.

When using `j!steal`, `res` and `prob` show up, `res` is a random value and
if it is greater than `prob`, you are arrested. `prob` is calculated using
the target's current wallet and the amount you want to steal from them.
"""

class JoseCoin(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)
        self.counter = 0

    def to_hours(self, seconds):
        if seconds is None:
            return 0
        return seconds / 60 / 60

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
        probability = jcommon.JC_PROBABILITY
        if message.author.id in self.stealdb['cdown']:
            # get type of cooldown
            # type 0 = arrest
            # type 1 = get more stealing points
            arrest_data = self.stealdb['cdown'][message.author.id]
            if arrest_data[1] == 0:
                probability /= 2

        if random.random() > probability:
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

        if range_max > 16:
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

        if range_max > 16:
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

    async def c_stealreset(self, message, args, cxt):
        '''`j!stealreset user` - reset an user's status in stealdb'''
        await self.is_admin(message.author.id)

        try:
            userid = args[1]
        except:
            await cxt.say("Error parsing userid")
            return

        res = []
        if userid in self.stealdb['points']:
            del self.stealdb['points'][userid]
            res.append('points')

        if userid in self.stealdb['cdown']:
            del self.stealdb['cdown'][userid]
            res.append('cdown')

        if userid in self.stealdb['period']:
            del self.stealdb['period'][userid]
            res.append('period')

        await cxt.say("Removed <@%s> from databases `%s`", (userid, ', '.join(res),))

    async def c_stealstat(self, message, args, cxt):
        # get status from person
        personid = message.author.id

        res = []

        points = self.stealdb['points'].get(personid, 3)
        cooldown = self.stealdb['cdown'].get(personid, None)
        grace_period = self.stealdb['period'].get(personid, None)

        res.append("**%s**, you have %d stealing points" % (str(message.author), points))
        if cooldown is not None:
            cooldown_sec, cooldown_type = cooldown
            cooldown_sec -= time.time()

            if cooldown_sec <= 0:
                res.append("A cooldown has ended %.2f hours ago, use `j!steal` to update" % \
                    (-self.to_hours(cooldown_sec)))

            if cooldown_type == 0:
                if cooldown_sec > 0:
                    res.append(":cop: you're in prison, %.2f hours remaining" % \
                        (self.to_hours(cooldown_sec),))
                else:
                    res.append(":helicopter: you got out of prison, %.2f hours ago" % \
                        (-self.to_hours(cooldown_sec),))
            elif cooldown_type == 1:
                if cooldown_sec > 0:
                    res.append(":alarm_clock: you're waiting for stealing points, %.2f hours remaining" % \
                        (self.to_hours(cooldown_sec),))
                else:
                    res.append(":alarm_clock: you got 3 stealing points, %.2f hours ago" % \
                        (-self.to_hours(cooldown_sec),))
            else:
                res.append(":warning: unknown cooldown type")

        if grace_period is not None:
            grace_period -= time.time()
            if grace_period > 0:
                res.append(":angel: you're in grace period, %.2f hours remaining" % \
                    (self.to_hours(grace_period),))
            else:
                res.append(":angel: you lost your grace period %.2f hours ago" % \
                    (-self.to_hours(grace_period)))

        await cxt.say('\n'.join(res))

    async def do_arrest(self, thief_id, amount, arrest_type=0):
        self.stealdb['cdown'][thief_id] = (time.time() + ARREST_TIME, arrest_type)
        if arrest_type == 0:
            # pay half the amount
            fine = amount / decimal.Decimal(2)
            return self.jcoin.transfer(thief_id, self.jcoin.jose_id, fine)

    async def c_steal(self, message, args, cxt):
        '''`j!steal @target amount` - Steal JoséCoins from someone'''

        if len(args) < 2:
            await cxt.say(self.c_steal.__doc__)
            return

        # parse mention
        try:
            target_id = await jcommon.parse_id(args[1], message)
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
                if remaining > 1:
                    await cxt.say(":cop: You are still in prison, wait %.2f hours", \
                        (self.to_hours(remaining),))
                    return
                else:
                    del self.stealdb['cdown'][thief_id]
                    await self.save_steal_db()

            elif cooldown_type == 1:
                if remaining > 1:
                    await cxt.say("Wait %.2f hours to regenerate your stealing points", \
                        (self.to_hours(remaining),))
                    return
                else:
                    del self.stealdb['points'][thief_id]
                    del self.stealdb['cdown'][thief_id]
                    await self.save_steal_db()

        stealuses = self.stealdb['points'].get(thief_id, None)
        if stealuses is None:
            self.stealdb['points'][thief_id] = stealuses = 3

        thief_user = message.author
        target_user = await self.client.get_user_info(target_id)

        grace_period = (self.stealdb['period'].get(target_id, 0) - time.time())
        if grace_period > 0:
            await cxt.say("Target is in :angel: grace period :angel:")
            await cxt.say("%s tried to steal %.2fJC from you, but you have %.2f hours of grace period", \
                target_user, (str(thief_user), amount, self.to_hours(grace_period)))
            return

        self.jcoin.data[thief_id]['times_stolen'] += 1

        if stealuses < 1:
            res = await self.do_arrest(thief_id, amount, 1)
            await cxt.say("You don't have any more stealing points, wait 8 hours to get more.")
            return

        if target_id == self.jcoin.jose_id:
            arrest = await self.do_arrest(thief_id, amount)
            await cxt.say(":cop: You can't steal from José. Arrested for 8h\n`%s`", (arrest[1],))
            return

        target_account = self.jcoin.get(target_id)[1]
        target_amount = target_account['amount']

        if amount > target_amount:
            # automatically in prison
            arrest = await self.do_arrest(thief_id, amount)
            await cxt.say(":cop: Arrested because you tried to steal more than the target has, 8h jail time.\n`%s`", \
                (arrest[1],))

        D = decimal.Decimal
        chance = (BASE_CHANCE + (target_amount / amount)) * D(0.3)
        if chance > 8: chance = 5

        res = random.random() * 10

        if res < chance:
            self.logger.info("Stealing %.2fJC from %s[%s] to %s[%s]", \
                amount, target_account['name'], target_id, message.author, thief_id)

            # steal went good, make transfer
            ok = self.jcoin.transfer(target_id, thief_id, amount)

            # check transfer status
            if not ok[0]:
                await cxt.say("jc->err: %s", ok[1])
            else:
                await cxt.say("`[res: %.2f < prob: %.2f]` Stealing went well, nobody noticed, you thief. \n`%s`", \
                    (res, chance, ok[1]))

                grace_period_hour = 3
                if target_id not in jcommon.ADMIN_IDS:
                    grace_period_hour = 6

                await cxt.say(":gun: You got robbed! The thief(%s) stole `%.2fJC` from you. %d hour grace period", \
                    target_user, (str(thief_user), amount, grace_period_hour))

                self.jcoin.data[thief_id]['success_steal'] += 1
                self.stealdb['period'][target_id] = time.time() + (grace_period_hour * 60 * 60)
                self.stealdb['points'][message.author.id] -= 1

        else:
            # type 0 cooldown, you got arrested
            arrest = await self.do_arrest(thief_id, amount)
            await cxt.say("`[res: %.2f > prob: %.2f]` :cop: Arrested! got 8h cooldown.\n`%s`", \
                (res, chance, arrest[1]))

        await self.save_steal_db()

    async def c_roubar(self, message, args, cxt):
        '''`j!roubar @target amount` - alias for `j!steal`'''
        await self.c_steal(message, args, cxt)

    async def c_taxes(self, message, args, cxt):
        '''`j!taxes` - show taxes from the server'''
        tbank_id = self.tbank_fmt(cxt)
        self.ensure_tbank(tbank_id)

        tbank = None
        _tbank = self.jcoin.get(tbank_id)
        if _tbank[0]:
            tbank = _tbank[1]

        if tbank is None:
            await cxt.say(":interrobang: tbank not found.")
            return

        await cxt.say("`%.2fJC in taxes`" % tbank['taxes'])

    async def sw_parse(self, message, args, cxt):
        try:
            amount = decimal.Decimal(args[1])
        except:
            await cxt.say("Error parsing `amount`")
            return None, None

        return amount

    async def c_store(self, message, args, cxt):
        '''`j!store amount` - Store JCs in bank'''

        if len(args) < 2:
            await cxt.say(self.c_store.__doc__)
            return

        to_store = await self.sw_parse(message, args, cxt)
        if to_store is None:
            return

        account = self.jcoin.data.get(message.author.id, None)
        if account is None:
            return

        if account['amount'] < to_store:
            await cxt.say(":octagonal_sign: You can't deposit more than what you have.")
            return

        account['amount'] -= to_store

        # user's personal bank
        account['fakemoney'] += to_store
        account['actualmoney'] += to_store

        await cxt.say("Transferred %.2fJC from %s account to personal bank.", \
            (to_store, account['name']))

    async def c_withdraw(self, message, args, cxt):
        '''`j!withdraw amount` - get JCs from your personal bank'''

        if len(args) < 2:
            await cxt.say(self.c_store.__doc__)
            return

        to_withdraw = await self.sw_parse(message, args, cxt)
        if to_withdraw is None:
            return

        account = self.jcoin.data.get(message.author.id, None)
        if account is None:
            return

        if account['actualmoney'] < to_withdraw:
            await cxt.say(":octagonal_sign: You can't withdraw more than what your personal bank has.")
            return

        # user's personal bank
        account['fakemoney'] -= to_withdraw
        account['actualmoney'] -= to_withdraw

        account['amount'] += to_withdraw

        await cxt.say("Transferred %.2fJC from personal bank to %s.", \
            (to_withdraw, account['name']))

    async def c_bank(self, message, args, cxt):
        '''`j!bank` - show bank status'''
        tbank_id = self.tbank_fmt(cxt)
        self.ensure_tbank(tbank_id)

        res = []
        tbank = self.jcoin.get(tbank_id)[1]

        storagebank_total = [0, 0]
        members_list = (m for m in message.server.members if m.id in self.jcoin.data)
        for member in members_list:
            account = self.jcoin.get(member.id)[1]
            storagebank_total[0] += account['actualmoney']
            storagebank_total[1] += account['fakemoney']

        res.append("Total in Taxbank: %.2fJC" % (tbank['taxes']))
        res.append("Total in Storagebank: %.2fJC, should have %.2fJC" % \
            (storagebank_total[0], storagebank_total[1]))

        account = None
        _account = self.jcoin.get(message.author.id)
        if _account[0]:
            account = _account[1]

        if account is not None:
            res.append("Total in personal bank: %.2fJC, should have %.2fJC" % \
                (account['actualmoney'], account['fakemoney']))

        await cxt.say(self.codeblock("", '\n'.join(res)))

    async def c_loan(self, message, args, cxt):
        '''`j!loan amount|"pay"|"see"` - loan money from your taxbank'''
        tbank_id = self.tbank_fmt(cxt)
        self.ensure_tbank(tbank_id)

        if len(args) < 2:
            await cxt.say(self.c_loan.__doc__)
            return

        if message.author.id not in self.jcoin.data:
            await cxt.say("You don't have a JC Account.")
            return

        pay = False
        see = False

        try:
            loan = decimal.Decimal(args[1])
        except:
            if args[1] == 'pay':
                pay = True
            elif args[1] == 'see':
                see = True
            else:
                await cxt.say("Error parsing arguments")
                return

        tbank = None
        _tbank = self.jcoin.get(tbank_id)
        if _tbank[0]:
            tbank = _tbank[1]

        if see:
            if message.author.id in tbank['loans']:
                await cxt.say("You loaned %.2fJC from this taxbank" % \
                    (tbank['loans'][message.author.id],))
            else:
                await cxt.say("You didn't loan from this taxbank.")
            return

        if not pay:
            if loan > tbank['taxes']:
                await cxt.say("You can't loan more than what taxbank has.")
                return

            if tbank['loans'].get(message.author.id, False):
                await cxt.say("You can't make another loan")
                return

            # make loan
            ok = self.jcoin.transfer(tbank_id, message.author.id, loan)
            if not ok[0]:
                await cxt.say("jc->err: %s", (ok[1],))
                return

            tbank['loans'][message.author.id] = loan
            await cxt.say("Loan successful. `%r`", (ok[1],))
        else:
            need_to_pay = tbank['loans'].get(message.author.id, None)
            if need_to_pay is None:
                await cxt.say("You don't need to pay nothing.")
                return

            ok = self.jcoin.transfer(message.author.id, tbank_id, need_to_pay)
            if not ok[0]:
                await cxt.say("jc->err: %s", (ok[1],))
                return

            del tbank['loans'][message.author.id]
            await cxt.say("Thanks! `%r`", (ok[1],))
