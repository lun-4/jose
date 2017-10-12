import time
import decimal
import logging
import collections
import asyncio
import pprint

import discord

from random import SystemRandom
from discord.ext import commands
from .common import Cog

log = logging.getLogger(__name__)
random = SystemRandom()


# JoséCoin constants
JOSECOIN_REWARDS = [0, 0, 0, 0.6, 0.7, 1, 1.2, 1.5, 1.7]

# cooldown reward: 40 minutes
REWARD_COOLDOWN = 1800

# Tax constant: used for tax increase calculation
# Probability constant: used for probability increase with your paid tax
TAX_CONSTANT = decimal.Decimal('1.0048')
PROB_CONSTANT = decimal.Decimal('1.003384590736')

# 1.2%
COIN_BASE_PROBABILITY = decimal.Decimal('0.012')


class TransferError(Exception):
    pass


TRANSFER_OBJECTS = [
    'bananas',
    'computers',
    'dogs',
    'memes',
    'cats',
    'coins',
    'paintings',
]


class Coins(Cog):
    def __init__(self, bot):
        super().__init__(bot)
        self.jcoin_coll = self.config.jose_db['josecoin']
        self.hidecoin_coll = self.config.jose_db['jcoin-hidecoin']

        self.BASE_PROBABILITY = COIN_BASE_PROBABILITY

        self.TransferError = TransferError
        self.bot.simple_exc.append(TransferError)

        # Reward cooldown dict
        self.reward_env = {}

        #: relates guilds to the accounts that are in the guild
        #  used by guild_accounts to speed things up
        self.acct_cache = collections.defaultdict(list)

        #: Used to prevent race conditions on guild_accounts
        self.gacct_locks = collections.defaultdict(asyncio.Lock)

        #: proper account cache, used by get_account
        self.cache = {}

        #: I hate locks
        self.transfer_lock = asyncio.Lock()

        #: I hate locks even more
        self.locked_accounts = []

    def get_name(self, user_id, account=None):
        """Get a string representation of a user or guild."""
        if isinstance(user_id, discord.Guild):
            return f'taxbank:{user_id.name}'
        elif isinstance(user_id, discord.User):
            return str(user_id)

        obj = self.bot.get_user(int(user_id))

        if obj is None:
            # try to find guild
            obj = self.bot.get_guild(user_id)
            if obj is not None:
                obj = f'taxbank:{obj}'

        if obj is None:
            # we tried stuff, show a special text
            if account:
                if account['type'] == 'user':
                    return f'Unfindable User {user_id}'
                elif account['type'] == 'guild':
                    return f'Unfindable Guild {user_id}'
                else:
                    return f'Unfindable Unknown {user_id}'
            else:
                return f'Unfindable ID {user_id}'

        return str(obj)

    def empty_account(self, account_id, account_type, amount):
        """Return an empty account object.

        Parameters
        ----------
        account_id: int
            ID of this account.
        account_type: str
            Account's type, can be ``"user"`` or ``"taxbank"``.
        amount: int or float or ``decimal.Decimal``
            Account's starting amount, only valid for user accounts.
        """
        if account_type == 'user':
            return {
                'type': 'user',
                'amount': str(decimal.Decimal(amount)),
                'id': account_id,

                # statistics for taxes
                'taxpaid': str(decimal.Decimal(0)),

                # j!steal stuff
                'times_stolen': 0,
                'success_steal': 0,

                # from what taxbank are you loaning from
                'loaning_from': None,

                # last tbank to get interest from
                'interest_tbank': '',
            }
        elif account_type == 'taxbank':
            return {
                'type': 'taxbank',
                'id': account_id,
                'amount': str(decimal.Decimal(0)),
                'loans': {},
            }

    async def new_account(self, account_id: int, account_type: str='user',
                          init_amount: int=0):
        """Create a new account.

        Updates the guild to user id list cache.
        """
        if (await self.get_account(account_id, True)) is not None:
            return False

        account = self.empty_account(account_id, account_type, init_amount)
        try:
            r = await self.jcoin_coll.insert_one(account)
            log.info('ACK insert: %s', r.acknowledged)
            self.cache[account_id] = account
            return True
        except:
            log.exception('Error creating a new account')
            return False

    async def sane(self):
        """Ensures that there is an account for José."""
        if not (await self.get_account(self.bot.user.id)):
            await self.new_account(self.bot.user.id, 'user', 'inf')

    async def ensure_taxbank(self, ctx):
        """Ensure a taxbank exists for the guild."""
        if ctx.guild is None:
            raise self.SayException("No guild was found to be a taxbank, "
                                    "don't do this command in a DM.")

        if await self.get_account(ctx.guild.id) is None:
            await self.new_account(ctx.guild.id, 'taxbank')

    def convert_account(self, account: dict) -> dict:
        """Converts an account's `amount` and `taxpaid`
        fields to `decimal.Decimal`.
        """
        if not account:
            return None

        new_account = dict(account)

        new_account['amount'] = decimal.Decimal(account['amount'])

        try:
            new_account['taxpaid'] = decimal.Decimal(account['taxpaid'])
        except KeyError:
            pass

        return new_account

    def unconvert_account(self, account: dict) -> dict:
        """Unconvert an account to its str keys."""
        if not account:
            return None

        new_account = dict(account)

        new_account['amount'] = str(account['amount'])

        try:
            new_account['taxpaid'] = str(account['taxpaid'])
        except KeyError:
            pass

        return new_account

    async def get_account(self, account_id: int,
                          override_cache: bool=False) -> dict:
        """Get a single account by its ID.

        This does necessary convertion of the `amount` field
        to `decimal.Decimal` for actual usage.

        Uses caching.

        NOTE: You can override caching calls when setting
        `override_cache` to True.
        """
        if account_id in self.cache and (not override_cache):
            return self.convert_account(self.cache[account_id])

        account = await self.jcoin_coll.find_one({'id': account_id})
        if not account:
            self.cache[account_id] = None
            return None

        c_account = self.convert_account(account)

        # if you don't read from the cache
        # you shouldn't write to it
        if not override_cache:
            self.cache[account_id] = c_account

        return c_account

    def cache_invalidate(self, user_id: int) -> 'NoneType':
        """Invalidate an account from the account cache."""
        try:
            self.cache.pop(user_id)
        except KeyError:
            pass

    async def get_accounts_type(self, acc_type: str) -> list:
        """Get all accounts that respect an account type.

        Doesn't use cache.
        """

        cur = self.jcoin_coll.find({'type': acc_type})

        accounts = []
        async for account in cur:
            accounts.append(self.convert_account(account))

        return accounts

    def lock_account(self, account_id: int):
        """Lock an account from transferring."""
        try:
            self.locked_accounts.index(account_id)
        except ValueError:
            self.locked_accounts.append(account_id)

    def unlock_account(self, account_id: int):
        """Unlock an account."""
        try:
            self.locked_accounts.remove(account_id)
        except ValueError:
            pass

    async def update_accounts(self, accounts: list):
        """Update accounts to the jcoin collection.

        This converts `decimal.Decimal` to `str` in the ``amount`` field
        so we maintain the precision of decimal while fetching/saving.

        Updates the cache.
        """
        total = 0

        for account in accounts:
            if account['amount'].is_finite():
                account['amount'] = round(account['amount'], 3)
                try:
                    account['taxpaid'] = round(account['taxpaid'], 4)
                except:
                    pass

            # update cache
            self.cache[account['id']] = self.convert_account(account)
            account = self.unconvert_account(account)

            res = await self.jcoin_coll.update_one({'id': account['id']},
                                                   {'$set': account})

            if res.modified_count > 1:
                log.warning('Updating more than supposed to')
            else:
                total += res.modified_count

        log.info('[update_accounts] Updated %d documents', total)

    async def transfer(self, id_from: int, id_to: int, amount):
        """Transfer coins from one account to another.

        If the account that is receiving the coins is a taxbank account,
        the account that is giving the coins gets its ``taxpaid``
        field increased.

        Parameters
        -----------
        id_from: int
            ID of the account that is giving the coins.
        id_to: int
            ID of the account that is receiving the coins.
        amount: int, float or ``decimal.Decimal``
            Amount of coins to be transferred.
            Will be converted to decimal and rounded to 3 decimal places.

        Raises
        ------
        TransferError
            If any checking or transfer error happens
        """
        await self.sane()
        await self.transfer_lock

        res = None

        try:
            if id_from == id_to:
                raise TransferError("Can't transfer from "
                                    "the account to itself")

            if amount > 200:
                raise TransferError('Transferring too much.')

            try:
                amount = decimal.Decimal(amount)
                amount = round(amount, 3)
            except:
                raise TransferError('Error converting to decimal.')

            if amount < .0009:
                raise TransferError('no small transfers kthx')

            if amount <= 0:
                raise TransferError('lul not zero')

            account_from = await self.get_account(id_from)
            if account_from is None:
                raise TransferError('Account to extract funds not found')

            account_to = await self.get_account(id_to)
            if account_to is None:
                raise TransferError('Account to give funds not found')

            from_amount = account_from['amount']
            if from_amount < amount:
                raise TransferError('Not enough funds '
                                    f'({from_amount} < {amount})')

            log.info(f'{self.get_name(account_from["id"])} > {amount} > '
                     f'{self.get_name(account_to["id"])}')

            if account_to['type'] == 'taxbank':
                account_from['taxpaid'] += amount

            account_from['amount'] -= amount
            account_to['amount'] += amount

            await self.update_accounts([account_from, account_to])
            res = f'{amount} was transferred from {self.get_name(account_from["id"])} to {self.get_name(account_to["id"])}'
        finally:
            self.transfer_lock.release()

        # since return can in theory stop
        # the finally block from executing
        if res:
            return res

    async def all_accounts(self, field='amount'):
        """Return all accounts in decreasing order of the selected field."""
        cur = self.jcoin_coll.find()
        accounts = await cur.to_list(length=None)

        if field != 'amount':
            accounts = [acc for acc in accounts if acc['type'] == 'user']

        return sorted(accounts, key=lambda account: float(account[field]),
                      reverse=True)

    async def guild_accounts(self, guild: discord.Guild,
                             field='amount') -> list:
        """Fetch all accounts that reference users that are in the guild.

        Uses caching.
        """

        lock = self.gacct_locks[guild.id]
        await lock

        accounts = []

        try:
            userids = None
            using_cache = False
            if guild.id in self.acct_cache:
                userids = self.acct_cache[guild.id]
                using_cache = True
            else:
                userids = [m.id for m in guild.members]

            for uid in userids:
                account = await self.get_account(uid)

                if account:
                    accounts.append(account)

                    if not using_cache:
                        self.acct_cache[guild.id].append(uid)
        finally:
            lock.release()

        # sanity check
        if lock.locked():
            lock.release()

        return sorted(accounts, key=lambda account: float(account[field]),
                      reverse=True)        

    async def zero(self, user_id: int):
        """Zero an account."""
        account = await self.get_account(user_id)
        if account is None:
            return

        return await self.transfer(user_id,
                                   self.bot.user.id,
                                   account['amount'])

    async def ranks(self, user_id: int, guild: discord.Guild) -> tuple:
        all_accounts = await self.all_accounts()

        all_ids = [account['id'] for account in all_accounts]

        guild_ids = [account['id'] for account in all_accounts if
                     guild.get_member(account['id']) is not None]

        guildrank = guild_ids.index(user_id) + 1
        globalrank = all_ids.index(user_id) + 1

        return guildrank, globalrank, len(guild_ids), len(all_ids)

    async def pricing(self, ctx, base_tax):
        """Tax someone. [insert evil laugh of capitalism]"""
        await self.ensure_taxbank(ctx)

        # yes ugly
        base_tax = decimal.Decimal(base_tax)
        try:
            account = await self.get_account(ctx.author.id)
            if not account:
                raise self.SayException('No JoséCoin account found to tax')

            tax = base_tax + (pow(TAX_CONSTANT, account['amount']) - 1)
            await self.transfer(ctx.author.id, ctx.guild.id, tax)
        except self.TransferError as err:
            raise self.SayException(f'TransferError: `{err.args[0]}`')

    async def get_probability(self, account: dict) -> float:
        """Get the coin probability of someone."""
        prob = COIN_BASE_PROBABILITY
        taxpaid = account['taxpaid']

        if taxpaid < 50:
            return prob

        prob += round((pow(PROB_CONSTANT, taxpaid) / 100), 5)
        if prob > 0.042:
            prob = 0.042
        return prob

    @commands.command()
    async def coinprob(self, ctx):
        """Show your probability of getting JoséCoins.

        The base probability is defined globally across all acounts.

        The more tax you pay, the more your probability to getting coins rises.

        The maximum probability is 4.20%/message.
        """
        account = await self.get_account(ctx.author.id)
        if not account:
            raise self.SayException('Account not found.')

        em = discord.Embed(title='Probability Breakdown of JCs per message')
        em.add_field(name='Base probability',
                     value=f'{COIN_BASE_PROBABILITY * 100}%')

        if account['taxpaid'] >= 50:
            em.add_field(name='Increase from tax paid',
                         value=f'{round(pow(PROB_CONSTANT, account["taxpaid"]), 5)}%')
            res = await self.get_probability(account)
            em.add_field(name='Total', value=f'{res * 100}%')

        await ctx.send(embed=em)

    async def on_message(self, message):
        # fuck bots
        if message.author.bot or message.guild is None:
            return

        author_id = message.author.id
        if author_id == self.bot.user.id:
            return

        account = await self.get_account(author_id)
        if not account:
            return

        if await self.bot.is_blocked(author_id):
            return

        if await self.bot.is_blocked_guild(message.guild.id):
            return

        if not isinstance(message.channel, discord.TextChannel):
            return

        # get prison data from CoinsExt
        coinsext = self.bot.get_cog('CoinsExt')
        if coinsext is None:
            log.warning('CoinsExt NOT LOADED.')
            return

        now = time.time()

        cdown = await coinsext.cooldown_coll.find_one({'user_id': author_id})
        if cdown is not None:
            if cdown['type'] == 0:
                if cdown['finish'] > now:
                    return

        last_cooldown = self.reward_env.get(author_id, 0)
        if now < last_cooldown:
            return

        prob = await self.get_probability(account)
        if random.random() > prob:
            return

        amount = random.choice(JOSECOIN_REWARDS)
        if amount == 0:
            return

        try:
            await self.transfer(self.bot.user.id, author_id, amount)
            self.reward_env[author_id] = time.time() + REWARD_COOLDOWN
            if message.guild.large:
                return

            hide = await self.hidecoin_coll.find_one({'user_id': author_id})
            if hide:
                return

            try:
                await message.add_reaction('💰')
            except:
                pass
        except:
            log.error('autocoin->err', exc_info=True)

    @commands.command()
    async def account(self, ctx):
        """Create a JoséCoin account.

        Use 'j!help Coins' to find other JoséCoin-related commands.
        """
        user = ctx.author
        success = await self.new_account(user.id)

        if success:
            mutual_guilds = [g for g in self.bot.guilds if g.get_member(user.id)]
            for guild in mutual_guilds:
                # The length check is required
                # since if a guild doesn't have its account cache
                # loaded and someone creates an account,
                # the guild account cache becomes a list with only 1 account
                # (the one being created)
                # and that won't change because of the guild_accounts god damn
                # cache check
                cache = self.acct_cache[guild.id]
                if len(cache) > 0:
                    self.acct_cache[guild.id].append(user.id)

        await ctx.success(success)

    @commands.command(name='transfer')
    async def _transfer(self, ctx, person: discord.User,
                        amount: decimal.Decimal):
        """Transfer coins to another person."""
        amount = round(decimal.Decimal(amount), 3)

        try:
            await self.transfer(ctx.author.id, person.id, amount)
            await ctx.send(f'Transferred {amount!s} '
                           f'{random.choice(TRANSFER_OBJECTS)} from '
                           f'{ctx.author!s} to {person!s}')
        except Exception as err:
            log.exception('Error while transferring')
            await ctx.send(f'error while transferring: `{err!r}`')

    @commands.command()
    async def wallet(self, ctx, person: discord.User = None):
        """See the amount of coins you currently have."""
        acc = None

        if person is not None:
            acc = await self.get_account(person.id)
        else:
            acc = await self.get_account(ctx.author.id)

        if not acc:
            return await ctx.send('Account not found.')

        await ctx.send(f'{self.get_name(acc["id"])} > '
                       f'`{acc["amount"]}`, paid `{acc["taxpaid"]}JC` as tax.')

    @commands.command()
    async def donate(self, ctx, amount: decimal.Decimal):
        """Donate to your server's taxbank."""
        await self.ensure_taxbank(ctx)
        amount = round(decimal.Decimal(amount), 3)

        await self.transfer(ctx.author.id, ctx.guild.id, amount)
        await ctx.send(f'Transferred {amount!s} '
                       f'from {ctx.author!s} to {self.get_name(ctx.guild)}')

    @commands.command()
    @commands.is_owner()
    async def write(self, ctx, person: discord.User, amount: decimal.Decimal):
        """Overwrite someone's wallet."""
        account = await self.get_account(person.id)
        if account is None:
            raise self.SayException('account not found you dumbass')

        amount = round(amount, 3)

        await self.jcoin_coll.update_one({'id': person.id},
                                         {'$set': {'amount': str(amount)}})
        self.cache_invalidate(person.id)

        await ctx.send(f'Set {self.get_name(account["id"])} to {amount}')

    @commands.command()
    async def hidecoins(self, ctx):
        """Toggle the reaction when you receive money, globally."""
        user = ctx.author
        query = {'user_id': user.id}
        ex = await self.hidecoin_coll.find_one(query)
        if ex is None:
            r = await self.hidecoin_coll.insert_one(query)
            if r.acknowledged:
                await ctx.message.add_reaction('\N{UPWARDS BLACK ARROW}')
            else:
                await ctx.not_ok()
        else:
            r = await self.hidecoin_coll.delete_many(query)
            dc = r.deleted_count
            if dc == 1:
                await ctx.message.add_reaction('\N{DOWNWARDS BLACK ARROW}')
            else:
                log.warning('[hidecoins] N-Nani?!?!?! %d deleted', dc)
                await ctx.not_ok()

    @commands.command()
    async def _hidecoin(self, ctx):
        """Show if you are hiding the coin reaction or not"""
        ex = await self.hidecoin_coll.find_one({'user_id': ctx.author.id})
        await ctx.send(f'Enabled: {bool(ex)}')

    @commands.command(hidden=True)
    async def jcgetraw(self, ctx):
        """Get your raw josécoin account"""
        start = time.monotonic()
        account = await self.get_account(ctx.author.id)
        end = time.monotonic()

        delta = round((end - start) * 1000, 2)

        account = pprint.pformat(account)
        await ctx.send(f'```py\n{account}\nTook {delta}ms.```')


def setup(bot):
    bot.add_cog(Coins(bot))
