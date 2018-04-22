import logging
import hashlib
import datetime
import re

import discord
from discord.ext import commands

from .common import Cog

log = logging.getLogger(__name__)


class Profile(Cog, requires=['config', 'coins']):
    def __init__(self, bot):
        super().__init__(bot)

        self.description_coll = self.config.jose_db['descriptions']

        regex = '([a-zA-Z0-9]| |\'|\"|\!|\%|\<|\>|\:|\.|\,|\;|\*|\~|\n)'
        self.description_regex = re.compile(regex)

    async def set_description(self, user_id: int, description: str):
        """Set the description for a user."""
        desc_obj = {
            'id': user_id,
            'description': description,
        }

        if await self.get_description(user_id) is not None:
            await self.description_coll.update_one({
                'id': user_id
            }, {'$set': desc_obj})
        else:
            await self.description_coll.insert_one(desc_obj)

    async def get_description(self, user_id):
        """Get the description for a user."""
        dobj = await self.description_coll.find_one({'id': user_id})
        if dobj is None:
            return None
        return dobj['description']

    def mkcolor(self, name):
        """Make a color value based on a username."""
        colorval = int(hashlib.md5(name.encode("utf-8")).hexdigest()[:6], 16)
        return discord.Colour(colorval)

    def delta_str(self, delta) -> str:
        """Convert a time delta to a "humanized" form"""
        seconds = delta.total_seconds()
        years = seconds / 60 / 60 / 24 / 365.25
        days = seconds / 60 / 60 / 24
        if years >= 1:
            return f'{years:.2f} years'
        else:
            return f'{days:.2f} days'

    async def fill_jcoin(self, account, user, em, ctx):
        ranks = await self.jcoin.get_ranks(user.id, ctx.guild.id)
        r_global, r_tax, r_guild = ranks['global'], ranks['taxes'], \
            ranks['local']

        guild_rank, global_rank = r_guild['rank'], r_global['rank']
        guild_accounts, all_accounts = r_guild['total'], r_global['total']
        tax_rank, tax_global = r_tax['rank'], r_tax['total']

        em.add_field(
            name='JC Rank',
            value=f'{guild_rank}/{guild_accounts}, '
            f'{global_rank}/{all_accounts} globally')

        em.add_field(name='JoséCoin Wallet', value=f'{account["amount"]}JC')
        em.add_field(name='Tax paid', value=f'{account["taxpaid"]}JC')

        em.add_field(
            name='Tax rank', value=f'{tax_rank} / {tax_global} globally')

        try:
            s_success = account['steal_success']
            s_uses = account['steal_uses']

            ratio = s_success / s_uses
            ratio = round((ratio * 100), 3)

            em.add_field(
                name='Stealing',
                value=f'{s_uses} tries, '
                f'{s_success} success, '
                f'ratio of success: {ratio}/steal')
        except ZeroDivisionError:
            pass

    async def fill_badges(self, ctx, embed):
        emojis = await self.pool.fetch("""
            select badges.emoji
            from badge_users
            join badges
            on badge_users.badge = badges.badge_id
            where user_id = $1
        """, ctx.author.id)

        if not emojis:
            return

        embed.add_field(name='Badges',
                        value=''.join((b['emoji'] for b in emojis)))

    @commands.command()
    @commands.guild_only()
    async def profile(self, ctx, *, user: discord.User = None):
        """Get profile cards."""
        if user is None:
            user = ctx.author

        maybe_member = ctx.guild.get_member(user.id)
        if maybe_member:
            user = maybe_member

        em = discord.Embed(title='Profile card',
                           colour=self.mkcolor(user.name))

        if user.avatar_url:
            em.set_thumbnail(url=user.avatar_url)

        raw_repr = await self.get_json('https://api.getdango.com/api/'
                                       f'emoji?q={user.name}')

        emoji_repr = ''.join(emoji['text'] for emoji in raw_repr['results'])
        em.set_footer(text=f'{emoji_repr} | User ID: {user.id}')

        if isinstance(user, discord.Member) and (user.nick is not None):
            em.add_field(name='Name', value=f'{user.nick} ({user.name})')
        else:
            em.add_field(name='Name', value=user.name)

        description = await self.get_description(user.id)
        if description is not None:
            em.add_field(name='Description', value=description)

        delta = datetime.datetime.utcnow() - user.created_at
        em.add_field(name='Account age', value=f'{self.delta_str(delta)}')

        try:
            account = await self.jcoin.get_account(user.id)
            await self.fill_jcoin(account, user, em, ctx)
        except self.jcoin.AccountNotFoundError:
            pass

        await self.fill_badges(ctx, em)
        await ctx.send(embed=em)

    @commands.command()
    async def setdesc(self, ctx, *, description: str = ''):
        """Set your profile card description."""
        description = description.strip()

        if len(description) > 80:
            raise self.SayException('3 long 5 me pls bring it down dud')

        notmatch = re.sub(self.description_regex, '', description)
        if notmatch:
            raise self.SayException('there are non-allowed characters.')

        if not description:
            raise self.SayException('pls put something')

        if description.count('\n') > 10:
            raise self.SayException('too many newlines')

        await self.set_description(ctx.author.id, description)
        await ctx.ok()

    @commands.group(aliases=['badges', 'b'])
    async def badge(self, ctx):
        """Profile badges."""
        pass

    @badge.command(name='show')
    async def badge_show(self, ctx, user: discord.User = None):
        """Show badges for a user"""
        if not user:
            user = ctx.author

        badges = await self.pool.fetch("""
            select user_id, badge, badges.name,
                   badges.emoji, badges.description
            from badge_users
            join badges
            on badge_users.badge = badges.badge_id
            where user_id = $1
        """, user.id)

        embed = discord.Embed(title=f'Badges for {user}')
        embed.description = ''

        for badge in badges:
            embed.description += (f'#{badge["badge"]} {badge["emoji"]} '
                                  f'`{badge["name"]}` '
                                  f'`{badge["description"]}`\n')

        await ctx.send(embed=embed)

    @badge.command(name='list')
    async def badge_list(self, ctx, page: int = 0):
        """List available badges for your profile."""
        badges = await self.pool.fetch("""
            select badge_id, name, emoji, description, price
            from badges
            limit 10
            offset ($1 * 10)
        """, page)

        embed = discord.Embed(title=f'Page {page} of badges')
        embed.description = ''

        for badge in badges:
            embed.description += (f' - #{badge["badge_id"]}, {badge["name"]}, '
                                  f'{badge["emoji"]} `{badge["description"]}` '
                                  f'`{badge["price"]}JC`\n')

        await ctx.send(embed=embed)

    @badge.command(name='buy')
    async def badge_buy(self, ctx, badge_id: int):
        """Buy a badge"""
        badge = await self.pool.fetchrow("""
            select name, emoji, description, price
            from badges
            where badge_id = $1
        """, badge_id)

        if not badge:
            raise self.SayException('No badge found with that ID.')

        await self.coins.transfer(ctx.author.id,
                                  self.bot.user.id, badge['price'])

        await self.pool.execute("""
            insert into badge_users (user_id, badge)
            values ($1, $2)
        """, ctx.author.id, badge_id)

        await ctx.ok()

    async def badge_remove(self, ctx, badge_id: int):
        # TODO: this
        pass

    @badge.command(name='bootstrap')
    @commands.is_owner()
    async def bootstrap(self, ctx):
        """Bootstrap a handful of badges"""
        badges = [
            [0, 'badger', '\N{OK HAND SIGN}', 'Bought a badge', 1],
            [1, 'angery', '<:blobangery:437365762597060618>',
                'i angery', 15],
            [2, 'yeboi', '<:yeboi:353997914332200961>',
                'The meaning of life', 34.5],
            [3, 'gay', '\N{RAINBOW}', 'im gay', 13],
        ]

        success = 0
        for badge in badges:
            try:
                await self.pool.execute("""
                    insert into badges (badge_id, name,
                        emoji, description, price)
                    values ($1, $2, $3, $4, $5)
                """, *badge)
                success += 1
            except Exception as err:
                await ctx.send(f'Failed on `{badge[0]}`: `{err!r}`')

        await ctx.send(f'{success} badges inserted (total {len(badges)})')

def setup(bot):
    bot.add_jose_cog(Profile)

