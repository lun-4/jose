import decimal
import time
import logging
from random import SystemRandom

import discord
from discord.ext import commands

from .common import Cog, CoinConverter

random = SystemRandom()
log = logging.getLogger(__name__)

PRICES = {
    'OPR': ('Operational tax', ('datamosh', 'youtube')),
    'API': ('API tax', ('xkcd', 'wolframalpha', 'weather', 'money',
            'urban', 'hh', 'e621')),
}


# steal constants
BASE_CHANCE = decimal.Decimal('1')
STEAL_CONSTANT = decimal.Decimal(0.42)

# default cooldown when you are arrested
ARREST_TIME = 6

# cooldown when you need to regen stealing points
STEAL_REGEN = 9


def make_default_points(ctx):
    """Default stealing points object for someone."""
    return {
        'user_id': ctx.author.id,
        'points': 3,
    }


def make_cooldown(thief, c_type=0, hours=8):
    return {
        'user_id': thief.id,
        'type': c_type,
        'finish': time.time() + (hours * 60 * 60),
    }


class CoinsExt(Cog, requires=['coins']):
    """More currency commands separated into another cog."""
    def __init__(self, bot):
        super().__init__(bot)
        self.cooldown_coll = self.config.jose_db['steal_cooldowns']
        self.points_coll = self.config.jose_db['steal_points']
        self.grace_coll = self.config.jose_db['steal_grace']
        self.owner = None

    async def show(self, ctx, accounts, *, field='amount', limit=10):
        res = []

        filtered = []

        for (idx, account) in enumerate(accounts):
            name = self.jcoin.get_name(account['id'], account=account)
            if 'Unfindable' in name:
                continue
            else:
                account['_name'] = name
                filtered.append(account)

        filtered = filtered[:limit]

        for (idx, account) in enumerate(filtered):
            res.append(f'{idx + 1:3d}. {account["_name"]:30s}'
                       f' -> {account[field]}')

        joined = '\n'.join(res)
        if len(joined) > 1950:
            await ctx.send('very big cant show: {len(joined)}')
        else:
            await ctx.send(f'```\n{joined}\n```')

    @commands.command()
    async def top(self, ctx, mode: str = 'g', limit: int = 10):
        """Shows top 10 of accounts.

        Available modes:
        - g: global, all accounts in José's database.
        - l: local, all accounts in this server/guild.
        - t: tax, all accounts in José's database, ordered
            by the amount of tax they paid.
        - b: taxbanks, all taxbanks, globally

        - p: poorest, globally
        - lp: local poorest
        """

        b = '\N{NEGATIVE SQUARED LATIN CAPITAL LETTER B}'
        if limit > 20 or limit < 1:
            await ctx.send('pls no')
            return

        if mode == 'l':
            accounts = await self.jcoin.guild_accounts(ctx.guild)
            await self.show(ctx, accounts, limit=limit)

        elif mode == 'g':
            all_accounts = await self.jcoin.all_accounts()
            accounts = filter(lambda a: a['type'] == 'user', all_accounts)
            await self.show(ctx, accounts, limit=limit)

        elif mode == 't':
            accounts = await self.jcoin.all_accounts('taxpaid')
            await self.show(ctx, accounts, field='taxpaid', limit=limit)

        elif mode == 'b' or mode == b:
            all_accounts = await self.jcoin.all_accounts()
            accounts = filter(lambda acc: acc['type'] == 'taxbank',
                              all_accounts)
            await self.show(ctx, accounts, limit=limit)

        elif mode == 'p':
            all_accounts = await self.jcoin.all_accounts()
            accounts = list(filter(lambda a: a['type'] == 'user', all_accounts))
            accounts = reversed(accounts)
            await self.show(ctx, accounts, limit=limit)

        elif mode == 'lp':
            accounts = await self.jcoin.guild_accounts(ctx.guild, 'amount')
            accounts = reversed(accounts)
            await self.show(ctx, accounts, limit=limit)

        else:
            raise self.SayException('mode not found')

    @commands.command(name='prices')
    async def _prices(self, ctx):
        """Show price information for commands."""
        res = (f'- `{ptype} - {self.prices[ptype]}JC`: {val[0]}, `{val[1]}`'
               for ptype, val in PRICES.items())
        await ctx.send('\n'.join(res))

    @commands.command()
    @commands.guild_only()
    async def taxes(self, ctx):
        """Get the amount of taxes your taxbank holds.

        All taxed commands have a base price you can check with "j!prices".
        However, the total tax you pay when using the command
        is defined by the base tax + some weird shit.

        Ok, "some weird shit" = maths, it is a constant that
        is raised to your current wallet's amount.
        """
        await self.jcoin.ensure_taxbank(ctx)
        taxbank = await self.jcoin.get_account(ctx.guild.id)
        await ctx.send(f'`{self.jcoin.get_name(ctx.guild)}: '
                       f'{taxbank["amount"]}`')

    async def add_cooldown(self, user, c_type=0, hours=ARREST_TIME):
        """Add a cooldown to an user:

        Cooldown types follow the same as :meth:`CoinsExt.check_cooldowns`
        """
        cdown = make_cooldown(user, c_type, hours)
        r = await self.cooldown_coll.insert_one(cdown)
        if not r.acknowledged:
            raise RuntimeError('mongo did a dumb')

        log.debug('Added cooldown %r[%d] -> %r', user, user.id, cdown)
        return hours

    async def remove_cooldown(self, cooldown):
        """Removes a cooldown and resets the stealing points
        entry if cooldown type is 1."""
        log.debug('Removed cooldown for uid %d', cooldown['user_id'])
        await self.cooldown_coll.delete_one(cooldown)
        if cooldown['type'] == 1:
            await self.points_coll.update_one({'user_id': cooldown['user_id']},
                                              {'$set': {'points': 3}})

    async def check_cooldowns(self, ctx):
        """Check if any cooldowns are applied to the thief.
        Removes them if the cooldowns are expired, sends a message if it isn't.

        Cooldown types:
        - 0: prison cooldown
        - 1: stealing points regen
        """

        thief = ctx.author
        now = time.time()
        cooldown = await self.cooldown_coll.find_one({'user_id': thief.id})

        if cooldown is None:
            return

        cooldown_type, cooldown_end = cooldown['type'], cooldown['finish']
        if now >= cooldown_end:
            await self.remove_cooldown(cooldown)
            return

        remaining = (cooldown_end - now) / 60 / 60
        remaining = round(remaining, 2)

        if cooldown_type == 0:
            raise self.SayException('You are in prison, wait'
                                    f' {remaining} hours')
        elif cooldown_type == 1:
            raise self.SayException('You are waiting for stealing points '
                                    f'to regen, {remaining} hours to go')

    async def check_grace(self, target):
        """Check if the target is in grace period or not."""
        now = time.time()
        grace = await self.grace_coll.find_one({'user_id': target.id})
        if grace is None:
            return

        if now < grace['finish']:
            grace_remaining = (grace['finish'] - now) / 60 / 60
            grace_remaining = round(grace_remaining, 2)
            raise self.SayException(f"Your target is in grace period, "
                                    f"it'll expire in {grace_remaining} hours")

    async def steal_points(self, ctx):
        """Removes 1 stealing point from the thief."""
        thief = ctx.author
        points = await self.points_coll.find_one({'user_id': thief.id})
        if points is None:
            default = make_default_points(ctx)
            await self.points_coll.insert_one(default)
            points = default

        if points['points'] < 1:
            await self.add_cooldown(thief, 1, STEAL_REGEN)
            raise self.SayException('You ran out of stealing points! '
                                    f'wait {STEAL_REGEN} hours.')

        await self.points_coll.update_one({'user_id': thief.id},
                                          {'$set':
                                           {'points': points['points'] - 1}})

        # Automatically put a cooldown when points reaches 0
        if (points['points'] - 1) < 1:
            await self.add_cooldown(thief, 1, STEAL_REGEN)

    async def add_grace(self, target, hours):
        """Add a grace period to the target.

        If there already is a grace object attached to the target,
        it gets removed
        """
        grace = await self.grace_coll.find_one({'user_id': target.id})
        if grace:
            await self.grace_coll.delete_one(grace)

        await self.grace_coll.insert_one({
            'user_id': target.id,
            'finish': time.time() + (hours * 60 * 60)
        })

    async def do_arrest(self, ctx, amount):
        thief = ctx.author
        fee = amount / 2
        hours = 0

        # make sure taxbank exists
        await self.jcoin.get_account(ctx.guild.id)

        log.debug('[steal] arresting %s[%d]', thief, thief.id)

        try:
            transfer_info = await self.jcoin.transfer(thief.id,
                                                      ctx.guild.id, fee)
            hours = await self.add_cooldown(thief)
        except self.jcoin.TransferError as err:
            # oh you are so fucked
            if 'enough' not in err.args[0]:
                raise self.SayException(f'wtf how did this happen {err!r}')

            thief_account = await self.jcoin.get_account(thief.id)
            amnt = thief_account['amount']
            transfer_info = await self.jcoin.transfer(thief.id,
                                                      ctx.guild.id, amnt)
            hours = await self.add_cooldown(thief, 0, ARREST_TIME + int(amnt))

        return hours, transfer_info

    @commands.command()
    @commands.guild_only()
    async def steal(self, ctx, target: discord.User, *, amount: CoinConverter):
        """Steal JoséCoins from someone.

        Obviously, this isn't guaranteed to have 100% success.
        The probability of success depends on the target's
        current wallet and the amount you want
        to steal from them.

        There are other restrictions to stealing:
            - You can't steal less than 0.01JC
            - You can't steal if you have less than 6JC
            - You can't steal from targets who are in grace period.
            - You have 3 "stealing points", you lose one every time
               you use the steal command successfully
            - You can't steal from José(lol).
            - You are automatically arrested if you try to steal more
               than the target's wallet
        """
        await self.jcoin.ensure_taxbank(ctx)
        thief = ctx.author

        if thief == target:
            raise self.SayException("You can't steal from yourself")

        thief_account = await self.jcoin.get_account(thief.id)
        target_account = await self.jcoin.get_account(target.id)

        if thief_account is None or target_account is None:
            raise self.SayException("One of you don't have a JoséCoin account")

        if amount <= .01:
            raise self.SayException('Minimum amount to steal needs to be'
                                    ' higher than `0.01JC`')

        if amount <= 0:
            raise self.SayException('haha good one :ok_hand:')

        if thief_account['amount'] < 6:
            raise self.SayException("You have less than `6JC`, "
                                    "can't use the steal command")

        if target_account['amount'] < 3:
            raise self.SayException('Target has less than `3JC`, '
                                    'cannot steal them')

        try:
            self.coins.lock_account(thief.id)
            self.coins.lock_account(target.id)

            await self.check_cooldowns(ctx)
            await self.check_grace(target)
            await self.steal_points(ctx)

            thief_account['times_stolen'] += 1
            await self.jcoin.update_accounts([thief_account])

            self.coins.unlock_account(thief.id)
            self.coins.unlock_account(target.id)

            if target_account['amount'] == self.coins.INF:
                hours, transfer_info = await self.do_arrest(ctx, amount)
                raise self.SayException(":cop: Hell no! You can't steal "
                                        "from whitelisted accounts, "
                                        f"{hours} hours of jail now\n"
                                        f"{transfer_info}")

            if amount > target_account['amount']:
                hours, transfer_info = await self.do_arrest(ctx, amount)
                raise self.SayException(f":cop: Arrested from trying to steal "
                                        "more than the target's wallet, "
                                        f"{hours} hours in jail\n"
                                        f"{transfer_info}")

            t_amnt = target_account['amount']
            chance = (BASE_CHANCE + (t_amnt / amount)) * STEAL_CONSTANT
            if chance > 5:
                chance = 5
            chance = round(chance, 3)

            res = random.uniform(0, 10)
            res = round(res, 3)

            log.info('[steal:cmd] chance=%.2f res=%.2f thief=%s[uid=%d]'
                     ' target=%s[uid=%d] amount=%.2f',
                     chance, res, thief, thief.id, target, target.id, amount)

            if res < chance:
                # successful steal
                thief_account = await self.jcoin.get_account(thief.id)
                thief_account['success_steal'] += 1
                await self.jcoin.update_accounts([thief_account])

                transfer_info = await self.jcoin.transfer(target.id,
                                                          thief.id, amount)

                # add grace period
                grace = 5
                if self.owner is None:
                    appinfo = await self.bot.application_info()
                    self.owner = appinfo.owner

                if target.id == self.owner.id:
                    grace = 6

                try:
                    await target.send(f':gun: You got robbed! Thief(`{thief}`) '
                                      f'stole `{amount}` from you. '
                                      f'{grace}h grace period')
                except:
                    pass

                await self.add_grace(target, grace)
                await ctx.send(f'`[res: {res} < prob: {chance}]` congrats lol'
                               f'\n{transfer_info}')
            else:
                # failure, get rekt
                hours, transfer_info = await self.do_arrest(ctx, amount)
                await ctx.send(f'`[res: {res} > prob: {chance}]` :cop: '
                               f'Arrested! {hours}h in jail\n{transfer_info}')
        finally:
            self.coins.unlock_account(thief.id)
            self.coins.unlock_account(target.id)

    @commands.command(aliases=['stealstatus'])
    async def stealstate(self, ctx):
        """Show your current state in the stealing business.

        Shows your current cooldown(jail/points) and grace period if any.
        """
        uobj = {'user_id': ctx.author.id}
        res = []
        now = time.time()

        cooldown = await self.cooldown_coll.find_one(uobj)
        grace = await self.grace_coll.find_one(uobj)
        points = await self.points_coll.find_one(uobj)

        if points is not None:
            res.append(f'You have {points["points"]} stealing '
                       'points left to use.')

        if cooldown is not None:
            cdowntype_str = ['Jail', 'Stealing points regen'][cooldown['type']]
            remaining = round((cooldown['finish'] - now) / 60 / 60, 2)
            expired = '**[expired]**' if remaining < 0 else ''
            res.append(f'{expired}Cooldown: `type: {cooldown["type"]}/'
                       f'{cdowntype_str}`, remaining: `{remaining}h`')

        if grace is not None:
            remaining = round((grace['finish'] - now) / 60 / 60, 2)
            expired = '**[expired]**' if remaining < 0 else ''
            res.append(f'{expired}Grace period: remaining: `{remaining}h`')

        if len(res) < 1:
            await ctx.send('No state found for you')
            return

        await ctx.send('\n'.join(res))

    @commands.command()
    @commands.is_owner()
    async def stealreset(self, ctx, *people: discord.User):
        """Reset someone's state in steal-related collections.

        Deletes cooldowns, points and grace, resetting them
        (cooldowns and points) to default on the person's
        next use of j!steal.
        """
        for person in people:
            # don't repeat stuff lol
            uobj = {'user_id': person.id}
            cd_del = await self.cooldown_coll.delete_one(uobj)
            pt_del = await self.points_coll.delete_one(uobj)
            gr_del = await self.grace_coll.delete_one(uobj)

            await ctx.send(f'Deleted {cd_del.deleted_count} documents in `cooldown`\n'
                           f'- {pt_del.deleted_count} in `points`\n'
                           f'- {gr_del.deleted_count} in `graces`')

    @commands.command()
    async def deadtxb(self, ctx):
        """Show dead taxbanks.

        Dead taxbanks are taxbanks that refer to
        non-existent servers/guilds.
        """

        all_taxbanks = await self.jcoin.get_accounts_type('taxbank')
        dead_txb = filter(lambda acc: (self.bot.get_guild(acc['id']) is None),
                          all_taxbanks)
        deadtxb_count = sum(1 for a in dead_txb)

        await ctx.send(f'There are {deadtxb_count} dead taxbanks.')

    @commands.command()
    async def jcstats(self, ctx):
        """Show global JoséCoin statistics."""
        em = discord.Embed()

        total_accs = await self.coins.jcoin_coll.count()
        total_users = await self.coins.jcoin_coll.count({'type': 'user'})
        total_txb = await self.coins.jcoin_coll.count({'type': 'taxbank'})

        em.add_field(name='Total transfers done currently',
                     value=self.coins.transfers_done)
        em.add_field(name='Total accounts', value=total_accs)
        em.add_field(name='Total user accounts', value=total_users)
        em.add_field(name='Total taxbanks', value=total_txb)

        coll = self.coins.jcoin_coll
        steals, success = 0, 0
        usermoney, taxmoney = decimal.Decimal(0), decimal.Decimal(0)

        async for account in coll.find():
            if account['id'] == self.bot.user.id:
                continue

            a = decimal.Decimal(account['amount'])
            if a == self.coins.INF:
                continue

            if account['type'] == 'taxbank':
                taxmoney += a
            else:
                usermoney += a
                steals += account['times_stolen']
                success += account['success_steal']

        #usermoney = round(usermoney, 3)
        #taxmoney = round(taxmoney, 3)

        em.add_field(name='Steals',
                     value=f'{steals} steals, {success} successes')

        em.add_field(name='Total user money',
                     value=f'`{usermoney}JC`')

        em.add_field(name='Total tax money',
                     value=f'`{taxmoney}JC`')

        em.add_field(name='Total money',
                     value=f'`{usermoney + taxmoney}JC`')
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(CoinsExt(bot))
