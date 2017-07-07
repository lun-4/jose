import time
import decimal
import logging

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

# 1.2%
COIN_BASE_PROBABILITY = 0.012


class TransferError(Exception):
    pass


TRANSFER_OBJECTS = [
    'bananas',
    'computers',
    'dogs',
    'memes',
    'cats',
    'coins',
    'paitings',
]


class Coins(Cog):
    def __init__(self, bot):
        super().__init__(bot)
        self.jcoin_coll = self.config.jose_db['josecoin']
        self.steal_coll = self.config.jose_db['jcoin-steal']

        self.BASE_PROBABILITY = COIN_BASE_PROBABILITY

        self.TransferError = TransferError
        self.bot.simple_exc.append(TransferError)

        # Reward cooldown dict
        self.reward_env = {}

    def get_name(self, user_id):
        if isinstance(user_id, discord.Guild):
            return f'taxbank:{user_id.name}'

        obj = discord.utils.get(self.bot.get_all_members(), id=int(user_id))

        if obj is None:
            # try to find guild
            obj = self.bot.get_guild(user_id)
            if obj is not None:
                obj = f'taxbank:{obj}'

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

    async def new_account(self, account_id, account_type='user', init_amount=3):
        if (await self.get_account(account_id)) is not None:
            return False

        account = self.empty_account(account_id, account_type, init_amount)
        try:
            await self.jcoin_coll.insert_one(account)
            return True
        except:
            log.error("Error creating account", exc_info=True)
            return False

    async def sane(self):
        """Ensures that there is an account for José."""
        if await self.get_account(self.bot.user.id) is None:
            await self.new_account(self.bot.user.id, 'user', 'inf')

    async def ensure_taxbank(self, ctx):
        """Ensure a taxbank exists for the guild."""
        if await self.get_account(ctx.guild.id) is None:
            await self.new_account(ctx.guild.id, 'taxbank')

    async def get_account(self, account_id):
        account = await self.jcoin_coll.find_one({'id': account_id})
        if account is None:
            return None

        account['amount'] = decimal.Decimal(account['amount'])

        try:
            account['taxpaid'] = decimal.Decimal(account['taxpaid'])
        except:
            pass

        return account

    async def update_accounts(self, accounts):
        """Update accounts to the jcoin collection."""
        for account in accounts:
            if account['amount'].is_finite():
                account['amount'] = round(account['amount'], 3)
                try:
                    account['taxpaid'] = round(account['taxpaid'], 4)
                except:
                    pass

            account['amount'] = str(account['amount'])

            try:
                account['taxpaid'] = str(account['taxpaid'])
            except:
                pass
            await self.jcoin_coll.update_one({'id': account['id']}, {'$set': account})

    async def transfer(self, id_from, id_to, amount):
        """Transfer coins from one account to another.

        If the account that is receiving the coins is a taxbank account,
        the account that is giving the coins gets its ``taxpaid`` field increased.

        Parameters
        -----------
        id_from: str
            ID of the account that is giving the coins.
        id_to: str
            ID of the account that is receiving the coins.
        amount: int, float or ``decimal.Decimal``
            Amount of coins to be transferred.

        Raises
        ------
        TransferError
            If any checking or transfer error happens
        """
        await self.sane()

        try:
            amount = decimal.Decimal(amount)
            amount = round(amount, 3)
        except:
            raise TransferError('Error parsing to decimal.')

        if amount < .001:
            raise TransferError('no small transfers kthx')

        if amount <= 0:
            raise TransferError('lul not zero')

        account_from = await self.get_account(id_from)
        if account_from is None:
            raise TransferError('Account to extract funds not found')

        account_to = await self.get_account(id_to)
        if account_to is None:
            raise TransferError('Account to give funds not found')

        if account_from['amount'] < amount:
            raise TransferError('Account doesn\'t have enough funds for this transaction')

        log.info(f'{self.get_name(account_from["id"])} > {amount} > {self.get_name(account_to["id"])}')

        if account_to['type'] == 'taxbank':
            account_from['taxpaid'] += amount

        account_from['amount'] -= amount
        account_to['amount'] += amount

        await self.update_accounts([account_from, account_to])
        return f'{amount} was transferred from {self.get_name(account_from["id"])} to {self.get_name(account_to["id"])}'

    async def all_accounts(self, field='amount'):
        """Return all accounts in decreasing order of the selected field."""
        cur = self.jcoin_coll.find()
        accounts = await cur.to_list(length=None)

        if field != 'amount':
            accounts = [acc for acc in accounts if acc['type'] == 'user']

        return sorted(accounts, \
            key=lambda account: float(account[field]), reverse=True)

    async def ranks(self, user_id, guild):
        all_accounts = await self.all_accounts()

        all_ids = [account['id'] for account in all_accounts]

        guild_ids = [account['id'] for account in all_accounts if \
            guild.get_member(account['id']) is not None]

        guildrank = guild_ids.index(user_id) + 1
        globalrank = all_ids.index(user_id) + 1

        return guildrank, globalrank, len(guild_ids), len(all_ids)

    async def pricing(self, ctx, price):
        await self.ensure_taxbank(ctx)
        try:
            await self.transfer(ctx.author.id, ctx.guild.id, price)
        except self.TransferError as err:
            raise self.SayException(f'TransferError: `{err.args[0]}`')

    async def on_message(self, message):
        author_id = message.author.id
        if author_id == self.bot.user.id:
            return

        account = await self.get_account(author_id)
        if account is None:
            return

        if not isinstance(message.channel, discord.TextChannel):
            return

        now = time.time()
        last_cooldown = self.reward_env.get(author_id, 0)
        if now < last_cooldown:
            return

        if random.random() > COIN_BASE_PROBABILITY:
            return

        amount = random.choice(JOSECOIN_REWARDS)
        if amount != 0:
            try:
                await self.transfer(self.bot.user.id, author_id, amount)
                self.reward_env[author_id] = time.time() + REWARD_COOLDOWN
                if not message.guild.large:
                    try:
                        await message.add_reaction('💰')
                    except:
                        pass
            except:
                log.error('autocoin->err', exc_info=True)

    @commands.command()
    async def account(self, ctx):
        """Create a JoséCoin account."""
        success = await self.new_account(ctx.author.id)
        await ctx.success(success)

    @commands.command(name='transfer')
    async def _transfer(self, ctx, person: discord.User, amount: decimal.Decimal):
        """Transfer coins to another person."""
        amount = round(decimal.Decimal(amount), 3)

        try:
            await self.transfer(ctx.author.id, person.id, amount)
            await ctx.send(f'Transferred {amount!s} {random.choice(TRANSFER_OBJECTS)} from {ctx.author!s} to {person!s}')
        except Exception as err:
            await ctx.send(f'rip: `{err!r}`')

    @commands.command()
    async def wallet(self, ctx, person: discord.User = None):
        """See the amount of coins you currently have."""
        acc = None
        if person is not None:
            acc = await self.get_account(person.id)
        else:
            acc = await self.get_account(ctx.author.id)

        if acc is None:
            await ctx.send('Account not found.')
            return

        await ctx.send(f'{self.get_name(acc["id"])} > `{acc["amount"]}`, paid `{acc["taxpaid"]}JC` as tax.')

    @commands.command()
    async def donate(self, ctx, amount: decimal.Decimal):
        """Donate to your server's taxbank."""
        await self.ensure_taxbank(ctx)
        amount = round(decimal.Decimal(amount), 3)

        await self.transfer(ctx.author.id, ctx.guild.id, amount)
        await ctx.send(f'Transferred {amount!s} from {ctx.author!s} to {self.get_name(ctx.guild)}')

    @commands.command()
    @commands.is_owner()
    async def write(self, ctx, person: discord.User, amount: decimal.Decimal):
        """Overwrite someone's wallet."""
        account = await self.get_account(person.id)
        if account is None:
            raise self.SayException('account not found you dumbass')
        
        amount = round(amount, 3)
        await self.jcoin_coll.update_one({'id': person.id}, {'$set': {'amount': float(amount)}})
        await ctx.send(f'Set {self.get_name(account["id"])} to {amount}')

def setup(bot):
    bot.add_cog(Coins(bot))
