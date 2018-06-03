import logging
import datetime
import decimal
from random import uniform

import discord
from discord.ext import commands

from .common import Cog, CoinConverter
from .utils import Table
from .coins import AccountType

log = logging.getLogger(__name__)

# steal constants
BASE_CHANCE = decimal.Decimal('1')
STEAL_CONSTANT = decimal.Decimal('0.42')

# 6 hours in jail by default
# 9 hours for point regen
DEFAULT_ARREST = 6
DEFAULT_REGEN = 9

# how many hours for grace periods
GRACE_PERIOD = 5


class CooldownTypes:
    prison = 'prison'
    points = 'points'


class CooldownError(Exception):
    pass


def fmt_tdelta(delta):
    """Remove the microseconds from a timedelta object."""
    return datetime.timedelta(days=delta.days, seconds=delta.seconds)


class CoinsExt(Cog, requires=['coins']):
    @property
    def coins2(self):
        return self.bot.get_cog('Coins2')

    async def show(self, ctx, accounts, *, field='amount', limit=10):
        """Show a list of accounts"""
        filtered = []

        for idx, account in enumerate(accounts):
            name = self.jcoin.get_name(account['account_id'], account=account)
            account['_name'] = name
            filtered.append(account)

            if len(filtered) == limit:
                break

        table = Table('pos', 'name', 'account id', field)
        for idx, account in enumerate(filtered):
            table.add_row(
                str(idx + 1), account['_name'], str(account['account_id']),
                str(account[field]))

        rendered = await table.render(loop=self.loop)

        if len(rendered) > 1993:
            await ctx.send(f'very big cant show: {len(rendered)}')
        else:
            await ctx.send(f'```\n{rendered}```')

    @commands.command()
    async def top(self, ctx, mode: str = 'g', limit: int = 10):
        """Show accounts by specific criteria.

        'global' means all accounts in josé.
        'local' means the accounts in the server/guild.

        modes:
        - g: global accounts ordered by amount.
        - l: local accounts ordered by amount.
        - t: tax, global accounts ordered by tax paid.
        - b: taxbanks, all taxbanks ordered by amount

        - p: global poorest.
        - lp: local poorest.
        """
        if limit > 30 or limit < 1:
            raise self.SayException('invalid limit')

        if mode == 'g':
            accounts = await self.coins.jc_get(
                '/wallets', {
                    'key': 'global',
                    'reverse': True,
                    'type': self.coins.AccountType.USER,
                    'limit': limit,
                })
        elif mode == 'l':
            accounts = await self.coins.jc_get(
                '/wallets', {
                    'key': 'local',
                    'guild_id': ctx.guild.id,
                    'reverse': True,
                    'limit': limit
                })
        elif mode == 't':
            accounts = await self.coins.jc_get('/wallets', {
                'key': 'taxpaid',
                'reverse': True,
                'limit': limit,
            })
            return await self.show(ctx, accounts, field='taxpaid', limit=limit)
        elif mode == 'b':
            accounts = await self.coins.jc_get('/wallets', {
                'key': 'taxbanks',
                'reverse': True,
                'limit': limit,
            })
        elif mode == 'p':
            accounts = await self.coins.jc_get('/wallets', {
                'key': 'global',
                'type': AccountType.USER,
                'limit': limit,
            })
        elif mode == 'lp':
            accounts = await self.coins.jc_get('/wallets', {
                'key': 'local',
                'guild_id': ctx.guild.id,
                'limit': limit,
            })
        else:
            raise self.SayException('mode not found')

        await self.show(ctx, accounts, limit=limit)

    @commands.command(name='prices')
    async def _prices(self, ctx):
        """Show price information about commands."""
        em = discord.Embed(title='Pricing', color=discord.Color(0x2192bc))
        descriptions = {
            'OPR': (
                'Operational tax for high-load commands',
                ('yt', 'datamosh'),
            ),
            'API': ('API tax (includes the NSFW commands)',
                    ('xkcd', 'wolframalpha', 'weather', 'money', 'urban')),
            'TRN': ('Translation tax', ('translate', )),
        }

        for category in self.prices:
            price = self.prices[category]
            em.add_field(
                name=f'Category: {category}, Price: {price}',
                value=f'{descriptions[category][0]}: '
                f'{", ".join(descriptions[category][1])}',
                inline=False)

        await ctx.send(embed=em)

    @commands.command(name='taxes')
    @commands.guild_only()
    async def taxes(self, ctx):
        """Show your taxbank's wallet."""
        await self.coins.ensure_taxbank(ctx)
        acc = await self.coins.get_account(ctx.guild.id)
        await ctx.send(f'`{self.coins.get_name(ctx.guild)}: {acc["amount"]}`')

    async def add_cooldown(self,
                           user,
                           c_type: str = 'prison',
                           hours: int = DEFAULT_ARREST) -> int:
        """Add a steal cooldown to a user.
        """

        # Yes, I know, SQL Inejection.
        await self.pool.execute(f"""
        INSERT INTO steal_cooldown (user_id, ctype, finish)
        VALUES ($1, $2, now() + interval '{hours} hours')
        """, user.id, c_type)

        return hours

    async def remove_cooldown(self, user, c_type: CooldownTypes):
        """Remove a cooldown from a user.
        
        This resets the user's steal points if we are
        removing a points cooldown.
        """
        user_id = user.id
        res = await self.pool.execute("""
        DELETE FROM steal_cooldown
        WHERE user_id=$1 AND ctype=$2
        """, user_id, c_type)

        log.debug(f'Removing cooldown type {c_type} for {user!s}[{user.id}]')

        _, deleted = res.split()
        deleted = int(deleted)
        if deleted and c_type == CooldownTypes.points:
            await self.pool.execute("""
            UPDATE steal_points
            SET points=3
            WHERE user_id=$1
            """, user_id)

    async def check_cooldowns(self, thief: discord.User):
        """Check if the current thief is with its cooldowns
        checked up.
        """
        now = datetime.datetime.utcnow()
        cooldowns = await self.pool.fetch("""
        SELECT ctype, finish FROM steal_cooldown
        WHERE user_id=$1
        """, thief.id)

        for cooldown in cooldowns:
            c_type, c_finish = cooldown['ctype'], cooldown['finish']
            if now >= c_finish:
                await self.remove_cooldown(thief, c_type)
                continue

            # in the case the cooldown isnt finished
            remaining = c_finish - now
            if c_type == 'prison':
                raise self.SayException('\N{POLICE CAR} You are still in '
                                        'prison, wait '
                                        f'{fmt_tdelta(remaining)} hours')

            elif c_type == 'points':
                raise self.SayException('\N{DIAMOND SHAPE WITH A DOT INSIDE}'
                                        ' You are waiting for steal points. '
                                        f'Wait {fmt_tdelta(remaining)} hours')

    async def check_grace(self, target: discord.User):
        """Check if the target is in grace period."""
        now = datetime.datetime.utcnow()
        grace = await self.pool.fetchrow("""
        SELECT finish FROM steal_grace
        WHERE user_id = $1
        """, target.id)

        if not grace:
            return

        if now < grace['finish']:
            remaining = grace['finish'] - now
            raise self.SayException('\N{BABY ANGEL} Your target is in'
                                    ' grace period. it will expire in'
                                    f' {fmt_tdelta(remaining)} hours')

    async def check_points(self, thief: discord.User):
        """Check if current thief has enough steal points,
        decrement 1 from them if thief has enough,
        puts cooldown if it reaches 0."""
        points = await self.pool.fetchrow("""
        SELECT points FROM steal_points
        WHERE user_id = $1
        """, thief.id)

        if not points:
            await self.pool.execute("""
            INSERT INTO steal_points (user_id)
            VALUES ($1)
            """, thief.id)
            points = {'points': 3}

        if points['points'] < 1:
            await self.add_cooldown(thief, CooldownTypes.points, DEFAULT_REGEN)
            raise self.SayException('\N{FACE WITH TEARS OF JOY}'
                                    ' You ran out of stealing points!'
                                    f' wait {DEFAULT_REGEN} hours.')

        await self.pool.execute("""
        UPDATE steal_points
        SET points = points - 1
        WHERE user_id = $1
        """, thief.id)

        if (points['points'] - 1) < 1:
            await self.add_cooldown(thief, CooldownTypes.points, DEFAULT_REGEN)

    async def add_grace(self, target: discord.User, hours: int):
        """Add a grace period to the target.

        Removes an existing grace period.
        """
        grace = await self.pool.fetch("""
        SELECT finish FROM steal_grace
        WHERE user_id = $1
        """, target.id)

        if grace:
            await self.pool.execute("""
            DELETE FROM steal_grace
            WHERE user_id = $1
            """, target.id)

        # Yes, I know, SQL injection, again.
        await self.pool.execute(f"""
        INSERT INTO steal_grace (user_id, finish)
        VALUES ($1, now() + interval '{hours} hours')
        """, target.id)

    async def arrest(self, ctx, amount: decimal.Decimal) -> tuple:
        """Arrest the thief.

        Returns
        -------
        tuple
            with information about the arrest,
            and how many hours does the thief get
            in prison.
        """
        thief = ctx.author
        guild = ctx.guild
        fee = amount / 2

        # maintain sanity
        await self.coins.ensure_ctx(ctx)

        log.debug(f'arresting {thief}[{thief.id}]')

        try:
            transfer_info = await self.coins.transfer_str(thief, guild, fee)
            # fee is paid, jail.
            hours = await self.add_cooldown(thief)
        except self.coins.ConditionError:
            # fee is not paid, BIG JAIL.
            thief_acc = await self.coins.get_account(thief)
            amnt = thief_acc['amount']

            # zero the wallet, convert 1jc to extra hour in jail
            transfer_info = await self.coins.zero(thief, ctx.guild.id)
            hours = await self.add_cooldown(thief, CooldownTypes.prison,
                                            DEFAULT_ARREST + int(amnt))

        return hours, transfer_info

    def info_arrest(self, hours: int, transfer_info: str, message: str):
        """Generate a SayException with the information on the autojail."""
        raise self.SayException(f'\N{POLICE OFFICER} You got '
                                f'arrested! {message}\n{hours}h in jail.\n'
                                f'`{transfer_info}`')

    def steal_info(self,
                   res: float,
                   chance: float,
                   transfer_info: str,
                   hours: int = None):
        """Show the information about the success / failure of a steal."""
        msg_res = [f'`[chance: {chance} | res: {res}]`']

        if res < chance:
            msg_res.append(f'Congrats!')
        else:
            msg_res.append(f'\N{POLICE OFFICER} Arrested!')
            msg_res.append(f'{hours}h in jail.')

        msg_res.append(transfer_info)
        raise self.SayException('\n'.join(msg_res))

    @commands.command(name='steal')
    @commands.guild_only()
    async def steal(self, ctx, target: discord.User, *, amount: CoinConverter):
        """Steal JoséCoins from someone.

        Obviously this does not have a 100% success rate,
        the best success you can achieve is a 50% rate.

        The probability of success depends on four factors:
        the base chance, the wallet of your target,
        the amount you want to steal from the wallet,
        and the steal constant.

        Rules:
         - You can't steal less than 0.01JC.
         - You can't steal if you have less than 6JC.
         - You can't steal more than double your current wallet.
         - You can't steal from targets who are in grace period.
         - You, by default, have 3 stealing points, and you lose
            one each time you use the steal command successfully.
         - You can't steal from José, it will automatically jail you.
         - You are automatically jailed if you try to steal
            more than your target's wallet.
        """
        c2 = self.coins
        await c2.ensure_ctx(ctx)
        thief = ctx.author

        if thief == target:
            raise self.SayException('You can not steal from yourself')

        # make sure both have accounts
        try:
            thief_acc = await c2.get_account(thief.id)
            target_acc = await c2.get_account(target.id)
        except c2.AccountNotFoundError:
            raise self.SayException("One of you don't have a JoséCoin wallet")

        if amount <= 0.01:
            raise self.SayException('\N{LOW BRIGHTNESS SYMBOL} '
                                    'Stealing too low.')

        if thief_acc['amount'] < 6:
            raise self.SayException("You have less than `6JC`, "
                                    "can't use the steal command")

        if target_acc['amount'] < 3:
            raise self.SayException('Target has less than `3JC`, '
                                    'cannot steal them')

        if amount > 2 * thief_acc['amount']:
            raise self.SayException('You can not steal more than double '
                                    'your current wallet amount.')

        try:
            await c2.lock(thief.id, target.id)

            await self.check_cooldowns(thief)
            await self.check_grace(target)
            await self.check_points(thief)

            await c2.jc_post(f'/wallets/{thief.id}/steal_use')
            await c2.unlock(thief.id, target.id)

            # checking for other stuff that cause autojail
            if target_acc['amount'] == -69:
                hours, transfer_info = await self.arrest(ctx, amount)
                self.info_arrest(hours, transfer_info,
                                 'You can not steal from this account.')

            t_amnt = target_acc['amount']
            if amount > t_amnt:
                hours, transfer_info = await self.arrest(ctx, amount)
                self.info_arrest(hours, transfer_info,
                                 'Trying to steal more than the target')

            chance = (BASE_CHANCE + (t_amnt / amount)) * STEAL_CONSTANT
            if chance > 5:
                chance = 5
            chance = round(chance, 3)

            res = uniform(0, 10)
            res = round(res, 3)

            log.info(f'[steal] chance={chance} res={res} amount={amount}'
                     f' t_amnt={t_amnt} '
                     f'thief={thief}[{thief.id}] target={target}[{target.id}]')

            success = res < chance

            # log steal
            await self.pool.execute("""
                insert into steal_history (thief, target, target_before,
                    amount, success, chance, res)
                values ($1, $2, $3, $4, $5, $6, $7)
            """, thief.id, target.id, t_amnt, amount, success, chance, res)

            if success:
                # success
                await c2.jc_post(f'/wallets/{thief.id}/steal_success')
                transfer_info = await c2.transfer_str(target.id, thief.id,
                                                      amount)

                grace = GRACE_PERIOD

                if t_amnt > 200:
                    # decrease grace period the richer you are
                    temp = t_amnt * (decimal.Decimal('0.3') * t_amnt)
                    grace -= (temp / amount) * decimal.Decimal(0.001)

                try:
                    grace_s = f'{grace}h grace period' if grace > 0 else \
                        '(NO GRACE AVAILABLE)'
                    await target.send(':gun: **You were robbed!** '
                                      f'The thief(`{thief}`) stole '
                                      f'{amount} from you. '
                                      f'{grace_s}')
                except:
                    pass

                if grace > 0:
                    await self.add_grace(target, GRACE_PERIOD)

                self.steal_info(res, chance, transfer_info)
            else:
                # jail
                hours, transfer_info = await self.arrest(ctx, amount)
                self.steal_info(res, chance, transfer_info, hours)
        finally:
            await c2.unlock(thief.id, target.id)

    @commands.command(name='stealstate', aliases=['stealstatus'])
    async def stealstate(self, ctx):
        """Show your current stealing state."""
        author = ctx.author
        now = datetime.datetime.utcnow()
        em = discord.Embed(title=f'Steal state for {author}')

        cooldowns = await self.pool.fetch("""
        SELECT ctype, finish FROM steal_cooldown
        WHERE user_id = $1
        """, author.id)
        grace = await self.pool.fetchrow("""
        SELECT finish FROM steal_grace
        WHERE user_id = $1
        """, author.id)
        points = await self.pool.fetchrow("""
        SELECT points FROM steal_points
        WHERE user_id = $1
        """, author.id)

        if points:
            em.add_field(
                name='remaining stealing points',
                value=points['points'],
                inline=False)

        for idx, cooldown in enumerate(cooldowns):
            c_type = cooldown['ctype']
            c_type_str = 'jail' if c_type == 'prison' else 'steal points regen'

            remaining = cooldown['finish'] - now
            r_sec = remaining.total_seconds()
            expired = ' [EXPIRED]' if r_sec < 0 else ''

            em.add_field(
                name=f'cooldown {idx}{expired}',
                value=f'{c_type_str}: `{fmt_tdelta(remaining)}`',
                inline=False)

        if grace:
            # get timedelta
            remaining = grace['finish'] - now
            r_sec = remaining.total_seconds()
            expired = '[EXPIRED] ' if r_sec < 0 else ''
            em.add_field(
                name=f'{expired}grace period',
                value=f'`{fmt_tdelta(remaining)}`',
                inline=False)

        await ctx.send(embed=em)

    @commands.command(name='stealreset')
    @commands.is_owner()
    async def stealreset(self, ctx, *people: discord.User):
        """Reset people's steal states."""
        for person in people:
            res = await self.pool.execute(f"""
            DELETE FROM steal_points WHERE user_id = {person.id};
            DELETE FROM steal_cooldown WHERE user_id = {person.id};
            DELETE FROM steal_grace WHERE user_id = {person.id};
            """)

            self.loop.create_task(ctx.send(f'`{person}: {res}`'))

    @commands.group(aliases=['txr'], invoke_without_command=True)
    async def taxreturn(self, ctx):
        """Manage tax returns.

        Depending on how much tax you've paid, you
        can request a tax return.

        The returned money is calculated based on all your
        transactions done to taxbanks.

        NOTE: Only transactions that were done at the
        time v3 was deployed are valid.

        Of course, not all transactions will apply
        to the tax return.

        Only tax transactions which are above 5JC will count
        to the total available tax return money.

        Plus, not all the "available tax return" money will
        be promptly available to withdraw, once you withdraw,
        only 10% of that amount is given to your wallet.
        """
        await ctx.invoke(self.bot.get_command('help'), 'txr')

    async def txr_transactions(self, user: discord.User) -> list:
        """Get all tax transactions done by the user.

        Only transactions that are above average count torwards
        the list.

        Returns
        -------
        list[asyncpg.Record]
            List of transactions that satisfy the criteria.
        """
        return await self.pool.fetch("""
        select *
        from transactions

        join accounts on transactions.receiver = accounts.account_id

        where transactions.sender=$1
         and accounts.account_type=1
         and transactions.amount >= 5
         and transactions.taxreturn_used = false
        """, user.id)

    async def txr_total(self, user: discord.User) -> decimal.Decimal:
        """Get the total amount of tax that is available
        to be returned to the user.
        """

        return await self.pool.fetchval("""
        select sum(transactions.amount) * 25/100
        from transactions

        join accounts on transactions.receiver = accounts.account_id

        where transactions.sender=$1
         and accounts.account_type=1
         and transactions.amount >= 5
         and transactions.taxreturn_used = false
        """, user.id)

    async def txr_not_total(self, user: discord.User) -> decimal.Decimal:
        return await self.pool.fetchval("""
        select sum(transactions.amount)
        from transactions

        join accounts on transactions.receiver = accounts.account_id

        where transactions.sender=$1
         and accounts.account_type=1
         and transactions.amount >= 5
         and transactions.taxreturn_used = false
        """, user.id)

    @taxreturn.command(name='query', aliases=['q'])
    async def taxreturn_check(self, ctx):
        """Check your tax return situation.

        Please, **PLEASE**, do 'j!help taxreturn' to
        understand how this works.

        Not reading the documentation then asking me
        how does it work will grant you a very angery girl,
        looking straight in your eyes, with fury in her eyes,
        wanting to kill you, with an AK-47.
        """
        total_avail = await self.txr_total(ctx.author)
        total_criteria = await self.txr_not_total(ctx.author)
        total_trans = await self.txr_transactions(ctx.author)

        em = discord.Embed(
            title='Tax return situation', color=discord.Color.gold())

        if not total_criteria:
            raise self.SayException("You don't have any transactions "
                                    "that meet criteria")

        em.add_field(
            name='Money that fits the criteria',
            value=f'`{round(total_criteria, 2)}JC`')
        em.add_field(
            name='Withdrawable money', value=f'`{round(total_avail, 2)}JC`')
        em.add_field(
            name='Tax transactions that meet criteria',
            value=f'{len(total_trans)}')

        await ctx.send(embed=em)

    @taxreturn.command(name='withdraw', aliases=['w'])
    async def taxreturn_withdraw(self, ctx):
        """Withdraw your available tax return money.

        This command has a cooldown of a week.
        """

        finish = await self.pool.fetchval("""
        select finish
        from taxreturn_cooldown
        where user_id = $1
        """, ctx.author.id)

        now = datetime.datetime.utcnow()

        if finish and finish > now:
            delta = finish - now
            raise self.SayException('\N{MANTELPIECE CLOCK}'
                                    f'You have to wait {fmt_tdelta(delta)}.')
        else:
            await self.pool.execute("""
            delete from taxreturn_cooldown
            where user_id = $1
            """, ctx.author.id)

        transactions = await self.txr_transactions(ctx.author)

        success, error = 0, 0
        sent = decimal.Decimal(0)

        log.debug(f'[txr] processing {ctx.author}, ' f'{len(transactions)}')

        for trans in transactions:
            # apply 10% to the amount

            # theres transactions.amount and accounts.amount
            # we do a filter to get the right one
            items = trans.items()
            t_amount = next(
                v for k, v in items if isinstance(v, decimal.Decimal))

            applied = t_amount * decimal.Decimal('0.25')

            # the reverse transaction, as tax return
            try:
                await self.jcoin.transfer(trans['receiver'], trans['sender'],
                                          applied)

                await self.pool.execute("""
                update transactions
                set taxreturn_used=true
                where idx=$1
                """, trans['idx'])

                success += 1
                sent += applied
            except self.coins.TransferError as err:
                log.exception('error on tax return reverse transfer op')
                await ctx.send('Error while transferring from '
                               f'`{self.jcoin.get_name(trans["receiver"])}` '
                               f'amount: `{applied}JC` '
                               f'`{err!r}`')

                error += 1

        sent = round(sent, 2)
        log.debug(f'[txr] {ctx.author}, {success} succ, '
                  f'{error} err, {sent}jc total')

        await ctx.send(f'{success} success transactions, '
                       f'{error} raised errors.\n'
                       f'You got `{sent}JC` from tax returns.')

        await self.pool.execute("""
        insert into taxreturn_cooldown (user_id, finish)
        values ($1, now() + interval '1 week')
        """, ctx.author.id)


def setup(bot):
    bot.add_jose_cog(CoinsExt)
