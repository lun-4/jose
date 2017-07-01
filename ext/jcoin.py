#!/usr/bin/env python3

import sys
sys.path.append("..")
import jauxiliar as jaux
import josecommon as jcommon
import decimal
import json
import os
import discord
import time

from random import SystemRandom
random = SystemRandom()

import motor.motor_asyncio

PRICE_TABLE = {
    'api': ('Tax for Commands that use APIs', jcommon.API_TAX_PRICE, \
            ('wolframalpha', 'temperature', 'money', 'bitcoin', 'xkcd', 'sndc', 'urban')),

    #'img': ('Price for all commands in `joseimages`', jcommon.IMG_PRICE, \
    #        ('derpibooru', 'hypno', 'e621', 'yandere')),

    'opr': ('Operational tax for commands that use a lot of processing', jcommon.OP_TAX_PRICE, \
            ('datamosh', 'yt'))
}

PERCENT = 1 * 100
HOUR = 60 * 60

LOAN_TAX = 25 / PERCENT
TAX_CONSTANT = decimal.Decimal(0.1)

DEC_PROBABILITY = decimal.Decimal(jcommon.JC_PROBABILITY)

# 40 minutes of cooldown between rewards
REWARD_COOLDOWN = 1800

# 1%
BASE_CHANCE = decimal.Decimal(1)
STEAL_CONSTANT = decimal.Decimal(0.42)
STEALDB_PATH = 'db/steal.json'
ARREST_TIME = 8 * HOUR

# lol
TATSUMAKI_ID = '172002275412279296'
MAX_LOAN = 20

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
        self.reward_env = {}

    def to_hours(self, seconds):
        if seconds is None:
            return 0
        return seconds / 60 / 60

    async def josecoin_save(self, message, dbg_flag=True):
        res = self.jcoin.save('jcoin/josecoin.db')
        if not res[0]:
            self.logger.error("jcerr: %r", res)

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
        if self.counter >= 20:
            res = await self.josecoin_save(message, False)
            if not res:
                self.logger.error("[jcoin:autosave] ERROR SAVING DB: %s", res[1])
                self.jcoin.lockdb()

            self.counter = 0

    async def e_on_message(self, message, cxt):
        author_id = message.author.id
        if author_id not in self.jcoin.data:
            return

        if message.channel.is_private:
            return

        now = time.time()
        last_cooldown = self.reward_env.get(author_id, 0)
        if now < last_cooldown:
            return

        # ugly solution, use all decimal
        probability = DEC_PROBABILITY

        account = self.jcoin.data[author_id]
        taxpaid = account['taxpaid']
        increase = (TAX_CONSTANT * taxpaid) / 100
        probability += decimal.Decimal(increase)

        if author_id in self.stealdb['cdown']:
            arrest_data = self.stealdb['cdown'][author_id]
            # type 0 = proper arrest
            if arrest_data[1] == 0:
                # remove all tax shit
                probability = jcommon.JC_PROBABILITY / 2

        # max 4.20%/message
        if probability > 0.0420:
            probability = decimal.Decimal(0.0420)

        if decimal.Decimal(random.random()) > probability or \
            cxt.env.get('jcflag', False):
            return

        amount = random.choice(jcommon.JC_REWARDS)
        if amount != 0:
            res = self.jcoin.transfer(self.jcoin.jose_id, author_id, amount)

            if res[0]:
                self.reward_env[author_id] = time.time() + REWARD_COOLDOWN
                try:
                    await self.client.add_reaction(message, '💰')
                except discord.NotFound:
                    await self.client.send_message(message.channel, f'💰 to {message.author}')
            else:
                jcommon.logger.error("do_josecoin->jc->err: %s", res[1])
                await cxt.say("jc->err: %s", (res[1],))

    async def c_jcprob(self, message, args, cxt):
        '''`j!jcprob` - show your JoséCoin probabilities'''
        self.sane_jcoin(cxt)
        author_id = message.author.id

        probability = decimal.Decimal(jcommon.JC_PROBABILITY)

        account = self.jcoin.data[author_id]
        taxpaid = account['taxpaid']
        increase = (TAX_CONSTANT * taxpaid) / 100
        probability += decimal.Decimal(increase)

        # max 4.20%/message
        if probability > 0.0420:
            probability = decimal.Decimal(0.0420)

        await cxt.say("`baseprob: %.2f%%/msg, tax_increase: %.2f%%, prob: %.2f%%/msg`", \
            (jcommon.JC_PROBABILITY * 100, increase * 100, probability * 100))

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
            account = res[1]

            res = []
            res.append(f'{account["name"]} -> `{account["amount"]:.3}`')

            actual = account["actualmoney"]
            fake = account["fakemoney"]

            if actual > 0 or fake > 0:
                res.append(f"Personal bank: `actual:{actual:.3} fake:{fake:.3}`")

            await cxt.say('\n'.join(res))
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
            await cxt.say(":thinking: `%r`", (e,))
            return

        self.jcoin.data[id_from]['amount'] = new_amount
        await cxt.say("<@%s> has %.2fJC now" % (id_from, \
            self.jcoin.data[id_from]['amount']))

        self.logger.info("%s Wrote %.2fJC to Account %s" % \
            (str(message.author), new_amount, id_from))

    async def c_jcsend(self, message, args, cxt):
        '''`j!jcsend @mention amount` - send JoséCoins to someone'''
        self.sane_jcoin(cxt)

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

    async def top10_parse(self, args, cxt):
        try:
            top_finish = int(args[1]) + 1
        except:
            top_finish = 11

        if top_finish > 17:
            await cxt.say("LimitError: values higher than 16 aren't valid")
            return
        elif top_finish <= 0:
            await cxt.say("haha no")
            return

        return top_finish

    async def top10_show(self, lst, finish, entry='amount'):
        res = []
        for (index, account_id) in enumerate(lst[:finish]):
            account = self.jcoin.data[account_id]
            res.append('%2d. %30s -> %.2f' % \
                (index, account['name'], account[entry]))
        return res

    async def c_ltop10(self, message, args, cxt):
        top_finish = await self.top10_parse(args, cxt)
        if top_finish is None:
            return

        _gaccounts = [userid for userid in self.jcoin.data \
            if message.server.get_member(userid) is not None]

        gacc_sorted = sorted(_gaccounts, key=lambda userid: \
            self.jcoin.data[userid]['amount'], reverse=True)

        res = await self.top10_show(gacc_sorted, top_finish)
        await cxt.say(self.codeblock("", '\n'.join(res)))
        return

    async def c_top10(self, message, args, cxt):
        top_finish = await self.top10_parse(args, cxt)
        if top_finish is None:
            return

        sorted_data = sorted(self.jcoin.data, key=lambda userid: \
            self.jcoin.data[userid]['amount'], reverse=True)

        res = await self.top10_show(sorted_data, top_finish)
        await cxt.say(self.codeblock("", '\n'.join(res)))
        return

    async def c_taxtop10(self, message, args, cxt):
        top_finish = await self.top10_parse(args, cxt)
        if top_finish is None:
            return

        _data = [userid for userid in self.jcoin.data if \
            self.jcoin.data[userid]['type'] == 0]

        sorted_data = sorted(_data, key=lambda userid: \
            self.jcoin.data[userid]['taxpaid'], reverse=True)

        res = await self.top10_show(sorted_data, top_finish, 'taxpaid')
        await cxt.say(self.codeblock("", '\n'.join(res)))
        return

    async def c_hsteal(self, message, args, cxt):
        await cxt.say(HELPTEXT_JC_STEAL)

    async def c_stealreset(self, message, args, cxt):
        '''`j!stealreset user` - reset a user's status in stealdb'''
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
        self.sane_jcoin(cxt)

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

        acc = self.jcoin.get(personid)[1]
        if acc['times_stolen'] < 1:
            res.append("You never stole before.")

        await cxt.say('\n'.join(res))

    async def do_arrest(self, thief_id, amount, arrest_type=0, tbank_id=None):
        self.stealdb['cdown'][thief_id] = (time.time() + ARREST_TIME, arrest_type)
        if arrest_type == 0:
            # pay half the amount
            fine = amount / decimal.Decimal(2)
            ok = self.jcoin.transfer(thief_id, tbank_id, fine)

            if ok[0]:
                return ok, 0
            else:
                # probably "account doesn't have enough funds to make this transaction" error
                # zero it
                thief_account = self.jcoin.data[thief_id]
                amount = thief_account['amount']
                ok = self.jcoin.transfer(thief_id, tbank_id, amount)
                if not ok:
                    self.logger.error("Error in do_arrest->jc_err: %r", ok)
                    return ok

                amount = int(amount)
                self.stealdb['cdown'][thief_id] = (time.time() + ARREST_TIME + amount, arrest_type)
                return ok, amount
        elif arrest_type == 1:
            return None, 0

    async def c_steal(self, message, args, cxt):
        '''`j!steal @target amount` - Steal JoséCoins from someone'''
        self.sane_jcoin(cxt)
        tbank_id = self.tbank_fmt(cxt)
        thief_id = str(message.author.id)

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

        # tfw hardcoded numbers
        if amount < .002:
            await cxt.say(f"Too low. Minimum is `0.002JC`")
            return

        if target_id not in self.jcoin.data:
            await cxt.say("The person you're trying to steal from doesn't have a JoséCoin account")
            return

        if thief_id == target_id:
            await cxt.say("You can't steal from yourself")
            return

        # flag is True if person can't steal from the victim
        flag = (target_id != TATSUMAKI_ID) and (self.jcoin.data[target_id]['times_stolen'] < 1)

        # check if anyone in the server is available to be stolen from
        available = False
        for member in cxt.server.members:
            acc_id = str(member.id)
            acc = self.jcoin.data.get(target_id)
            if acc is None: continue
            if acc['times_stolen'] > 0:
                available = True

        if message.author == cxt.server.owner and not available:
            # no one is available to steal from, the owner can steal from anybody
            flag = False

        if flag:
            await cxt.say("You can't steal from someone who never used the steal command.")
            return

        if amount <= 0:
            await cxt.say("good one haha :ok_hand: actually no")
            return

        if self.jcoin.data[thief_id]['amount'] < 3:
            await cxt.say("You have less than `3`JC, can't use the steal command")
            return

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
        target_user = discord.utils.get(self.client.get_all_members(), id=target_id)

        if target_user is None:
            target_user = await self.client.get_user_info(target_id)

        grace_period = (self.stealdb['period'].get(target_id, 0) - time.time())
        if grace_period > 0:
            await cxt.say("Target is in :angel: grace period :angel:")
            await cxt.say("%s tried to steal %.2fJC from you, but you have %.2f hours of grace period", \
                target_user, (str(thief_user), amount, self.to_hours(grace_period)))
            return

        self.jcoin.data[thief_id]['times_stolen'] += 1

        if stealuses < 1:
            arrest, extra = await self.do_arrest(thief_id, amount, 1, tbank_id)
            await cxt.say("You don't have any more stealing points, wait 8 hours to get more.")
            return

        if target_id == self.jcoin.jose_id:
            arrest, extra = await self.do_arrest(thief_id, amount, 0, tbank_id)
            await cxt.say(":cop: You can't steal from José. Arrested for %.2fh\n`%s`", \
                ((8 + extra), arrest[1]))
            return

        target_account = self.jcoin.get(target_id)[1]
        target_amount = target_account['amount']

        if amount > target_amount:
            # automatically in prison
            arrest, extra = await self.do_arrest(thief_id, amount, 0, tbank_id)
            await cxt.say(":cop: Arrested because you tried to steal more than the target has, %.2fh jail time.\n`%s`", \
                ((8 + extra), arrest[1]))
            return

        chance = (BASE_CHANCE + (target_amount / amount)) * STEAL_CONSTANT
        if chance > 5: chance = 5

        res = random.uniform(0, 10)

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
                if target_id in jcommon.ADMIN_IDS:
                    grace_period_hour = 6

                await cxt.say(":gun: You got robbed! The thief(%s) stole `%.2fJC` from you. %d hour grace period", \
                    target_user, (str(thief_user), amount, grace_period_hour))

                self.jcoin.data[thief_id]['success_steal'] += 1
                self.stealdb['period'][target_id] = time.time() + (grace_period_hour * 60 * 60)
                self.stealdb['points'][message.author.id] -= 1

        else:
            # type 0 cooldown, you got arrested
            arrest, extra = await self.do_arrest(thief_id, amount, 0, tbank_id)
            await cxt.say("`[res: %.2f > prob: %.2f]` :cop: Arrested! got %.2fh cooldown.\n`%s`", \
                (res, chance, (8 + extra), arrest[1]))

        await self.save_steal_db()

    async def c_roubar(self, message, args, cxt):
        '''`j!roubar @target amount` - alias for `j!steal`'''
        await self.c_steal(message, args, cxt)

    async def c_taxes(self, message, args, cxt):
        '''`j!taxes` - show taxes from the server'''
        tbank_id = self.tbank_fmt(cxt)
        self.ensure_tbank(tbank_id)

        tbank = self.jcoin.get(tbank_id)[1]

        if tbank is None:
            await cxt.say(":interrobang: tbank not found.")
            return

        await cxt.say("`%.2fJC in taxes`", (tbank['taxes'],))

    async def sw_parse(self, args, cxt):
        try:
            amount = decimal.Decimal(args[1])
        except:
            await cxt.say("Error parsing `amount`")
            return None, None

        return amount

    async def c_store(self, message, args, cxt):
        '''`j!store amount` - Store JCs in bank'''
        self.sane_jcoin(cxt)

        if len(args) < 2:
            await cxt.say(self.c_store.__doc__)
            return

        to_store = await self.sw_parse(args, cxt)
        if not isinstance(to_store, decimal.Decimal):
            return

        account = self.jcoin.data.get(message.author.id, None)

        if account['loaning_from'] is not None:
            await cxt.say("You can't store when you have a loan.")
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
        self.sane_jcoin(cxt)

        if len(args) < 2:
            await cxt.say(self.c_withdraw.__doc__)
            return

        to_withdraw = await self.sw_parse(args, cxt)
        if to_withdraw is None:
            return

        account = self.jcoin.data.get(message.author.id, None)

        if account['loaning_from'] is not None:
            await cxt.say("You can't withdraw when you have a loan.")
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
        self.sane_jcoin(cxt)

        if len(args) < 2:
            await cxt.say(self.c_loan.__doc__)
            return

        pay = False
        see = False
        account = self.jcoin.data[message.author.id]

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

        if (account['loaning_from'] is not None) and (account['loaning_from'] != tbank_id):
            await cxt.say("You aren't allowed to use `j!loan` in taxbanks different from the one you loaned from")
            return

        if account['fakemoney'] > 0:
            await cxt.say("You can't loan when you're storing money")
            return

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

            if loan > MAX_LOAN:
                await cxt.say("You can't make a loan higher than 20JC.")
                return

            if tbank['loans'].get(message.author.id, False):
                await cxt.say("You can't make another loan")
                return

            # make loan
            ok = self.jcoin.transfer(tbank_id, message.author.id, loan)
            if not ok[0]:
                await cxt.say("jc->err: %s", (ok[1],))
                return

            loan += (loan * decimal.Decimal(LOAN_TAX))
            tbank['loans'][message.author.id] = loan
            account['loaning_from'] = tbank_id

            await cxt.say("Loan successful. `%r`, you need to pay %.2fJC(loan + 25%% tax) later", \
                (ok[1], loan))
        else:
            need_to_pay = tbank['loans'].get(message.author.id)
            if need_to_pay is None:
                await cxt.say("You don't need to pay anything.")
                return

            ok = self.jcoin.transfer(message.author.id, tbank_id, need_to_pay)
            if not ok[0]:
                await cxt.say("jc->err: %s", (ok[1],))
                return

            del tbank['loans'][message.author.id]
            account['loaning_from'] = None
            await cxt.say("Thanks! `%r`", (ok[1],))

    async def c_loanreset(self, message, args, cxt):
        '''`j!loanreset userid` - reset an user's status in a taxbank'''
        await self.is_admin(message.author.id)

        try:
            userid = args[1]
        except:
            await cxt.say("Error parsing userid")
            return

        tbank_id = self.tbank_fmt(cxt)
        self.ensure_tbank(tbank_id)

        tbank = None
        _tbank = self.jcoin.get(tbank_id)
        if _tbank[0]:
            tbank = _tbank[1]

        account = self.jcoin.data[message.author.id]
        need_to_pay = tbank['loans'].get(message.author.id, None)
        del tbank['loans'][message.author.id]
        account['loaning_from'] = None

        await cxt.say("Removed <@%s> loan record of %.2fJC to pay", \
            (userid, need_to_pay,))

    async def c_donate(self, message, args, cxt):
        '''`j!donate amount` - donate to your server\'s Taxbank'''
        self.sane_jcoin(cxt)

        if len(args) < 2:
            await cxt.say(self.c_donate.__doc__)
            return

        try:
            amount = decimal.Decimal(args[1])
        except:
            await cxt.say("Error parsing `amount`")
            return

        c = await self.jcoin_pricing(cxt, amount)
        if c:
            await cxt.say("Donated %.2fJC in taxes.", (amount,))

    async def c_migrate(self, message, args, ctx):
        """Migrate from JSON to MongoDB.    JSON SUCKS ASS."""
        await self.is_admin(message.author.id)

        # create mongo client
        client = motor.motor_asyncio.AsyncIOMotorClient()

        josedb = client['jose-migration']
        jcoin_coll = jose['josecoin']

        res = await jcoin_coll.delete_many({})
        await ctx.say(f'Deleted `{res.deleted_count}` documents')

        inserted = 0

        for account_id in self.jcoin.data:
            account = self.jcoin[account_id]
            new_account = None

            if account['type'] == 0:
                new_account = {
                    'id': int(account_id),
                    'type': 'user',
                    'amount': str(account['amount']),
                    'taxpaid': str(account['taxpaid']),
                    'times_stolen': account['times_stolen'],
                    'success_steal': account['success_steal'],
                }
            elif account['type'] == 1:
                new_account = {
                    'id': int(account_id),
                    'type': 'taxbank',
                    'amount': str(account['taxes']),
                    'loans': {},
                }

            res = await jcoin_coll.insert_one(new_account)
            if res.acknowledged: inserted += 1

        await ctx.say(f'Inserted {inserted} documents, {len(self.jcoin.data)} total accounts')

