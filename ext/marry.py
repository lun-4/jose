import logging
import asyncio
import collections

import discord

from discord.ext import commands

from .common import Cog

log = logging.getLogger(__name__)


class Marry(Cog):
    """Relationships."""
    def __init__(self, bot):
        super().__init__(bot)
        self.locks = collections.defaultdict(bool)

    async def get_rels(self, user_id: int) -> list:
        rels = await self.pool.fetch("""
            select rel_id from relationships
            where user_id = $1
        """, user_id)

        return [row['rel_id'] for row in rels]

    async def get_users(self, rel_id: int) -> list:
        uids = await self.pool.fetch("""
            select user_id from relationships
            where rel_id = $1
        """, rel_id)

        if not uids:
            return []

        return [row['user_id'] for row in uids]

    @commands.command()
    @commands.guild_only()
    async def marry(self, ctx, who: discord.Member, rel_id: int = None):
        """Request someone to be in a relationship with you.

        Giving a relationship ID will turn that relationship into a
        poly (more than two) relationship.

        You do not use the relationship ID given here to claim an ID.

        Relationship IDs are generated based on
        the last one generated, plus one.
        """
        new_relationship = rel_id is None

        if who.bot:
            raise self.SayException('no bots allowed')

        if who == ctx.author:
            raise self.SayException('no selfcest allowed')

        if rel_id:
            users = await self.get_users(rel_id)

            if not users:
                raise self.SayException('Relationship not found.')

            if ctx.author.id not in users:
                raise self.SayException('You are not in '
                                        f'relationship id {rel_id}')

            if who.id in users:
                raise self.SayException('This person is already '
                                        f'in relationship id {rel_id}')

        restraint = await self.pool.fetchrow("""
        select user1, user2
        from restrains
        where user1 = $1 or user2 = $2
        """, ctx.author.id, who.id)

        if restraint is not None:
            return await ctx.send(f"You can not marry {who}.")

        # get all relationships
        rels = await self.get_rels(ctx.author.id)
        for in_rel_id in rels:
            users = await self.get_users(in_rel_id)
            if who.id in users:
                raise self.SayException('You are already with this person '
                                        f'(relationship id {in_rel_id})')

        if self.locks[who.id]:
            raise self.SayException('Please wait.')

        self.locks[who.id] = True

        # critical session
        try:
            await ctx.send(f'{who.mention}, {ctx.author.mention} has just '
                           'proposed to you. Do you agree to marry them?\n'
                           'Reply with y/n.')

            def yn_check(msg):
                cnt = msg.content.lower()
                chk1 = msg.author == who and msg.channel == ctx.channel
                chk2 = any(x == cnt for x in ['yes', 'no', 'y', 'n'])
                return chk1 and chk2

            try:
                message = await self.bot.wait_for('message',
                                                  timeout=30,
                                                  check=yn_check)
            except asyncio.TimeoutError:
                raise self.SayException(f'{ctx.author.mention}, '
                                        'timeout reached.')

            if message.content.lower() in ['no', 'n']:
                raise self.SayException(f'Invite denied, {ctx.author.mention}')
        finally:
            self.locks[who.id] = False

        # get next available id
        if not rel_id:
            new_rel_id = await self.pool.fetchval("""
                select max(rel_id) + 1 from relationships
            """)

            if not new_rel_id:
                new_rel_id = 1

            rel_id = new_rel_id

        # guarantee we don't fuck up on our polycules
        # by making this a proper transaction
        log.info(f'putting {ctx.author.id} <=> {who.id} to {rel_id}')

        async with self.pool.acquire() as conn:
            stmt = await conn.prepare("""
                insert into relationships (user_id, rel_id)
                values ($1, $2)
            """)

            if new_relationship:
                await stmt.fetchval(ctx.author.id, rel_id)
            await stmt.fetchval(who.id, rel_id)

        await ctx.send('All good!')

    @commands.command()
    async def relations(self, ctx, who: discord.User = None):
        """Show relationships the user is in.
        """
        if not who:
            who = ctx.author

        rel_ids = await self.pool.fetch("""
            select rel_id from relationships
            where user_id = $1
        """, who.id)

        if not rel_ids:
            raise self.SayException("You don't have any relationships")

        rel_ids = [row['rel_id'] for row in rel_ids]

        rels = {rel_id: await self.get_users(rel_id)
                for rel_id in rel_ids}
        res = []

        for rel_id, user_ids in rels.items():
            user_ids.remove(who.id)
            user_list = ', '.join(self.jcoin.get_name(uid)
                                  for uid in user_ids)

            res.append(f'#{rel_id}: `{user_list}`')

        await ctx.send('\n'.join(res))

    @commands.command(aliases=['divorce'])
    async def breakup(self, ctx, rel_id: int):
        """Remove yourself from a relationship."""
        users = await self.get_users(rel_id)
        if not users:
            raise self.SayException('Relationship not found')

        if ctx.author.id not in users:
            raise self.SayException('You are not in this relationship.')

        log.debug(f'breakup {ctx.author.id} from rel {rel_id}')

        await self.pool.execute("""
            delete from relationships
            where user_id = $1 and rel_id = $2
        """, ctx.author.id, rel_id)

        users = await self.get_users(rel_id)
        if len(users) < 2:
            log.info(f'deleting relationship {rel_id}: can not sustain')

            await self.pool.execute("""
                delete from relationships
                where rel_id = $1
            """, rel_id)

        await ctx.ok()

    @commands.command()
    async def restrain(self, ctx, user: discord.User):
        """Restrain someone from marrying you."""
        if user == ctx.author:
            return await ctx.send('no')

        restraint = await self.pool.fetchrow("""
        SELECT user1
        FROM restrains
        WHERE user1 = $1 AND user2 = $2
        """, ctx.author.id, user.id)

        if restraint is not None:
            return await ctx.send('To remove a restraint, use '
                                  f'`{ctx.prefix}restrainoff`')

        await self.pool.execute("""
        INSERT INTO restrains (user1, user2)
        VALUES ($1, $2)
        """, ctx.author.id, user.id)

        await ctx.ok()

    @commands.command()
    async def restrainoff(self, ctx, user: discord.User):
        """Remove a restraint."""
        user2 = await self.pool.fetchval("""
        select user2
        from restrains
        where user1 = $1 and user2 = $2
        """, ctx.author.id, user.id)

        if not user2:
            return await ctx.send("You don't have any restraints to "
                                  "that person")

        await self.pool.execute("""
        DELETE FROM restrains
        WHERE user1 = $1 AND user2 = $2
        """, ctx.author.id, user.id)

        await ctx.ok()


def setup(bot):
    bot.add_jose_cog(Marry)
