# -*- coding: utf-8 -*-

import asyncio
import logging

import asyncpg
import discord

from .common import Cog
from .utils import Timer
from jose import JoseBot


log = logging.getLogger(__name__)


class State(Cog, requires=['config']):
    """Synchronizes José's state to the PostgreSQL database for the JoséCoin REST API."""

    def __init__(self, bot: JoseBot):
        super().__init__(bot)

        self.loop.create_task(self.full_sync())

    @property
    def db(self) -> asyncpg.pool.Pool:
        cfg = self.bot.get_cog('Config')
        if cfg is not None:
            return cfg.db
        raise RuntimeError('Required config Cog is not loaded.')

    async def on_member_join(self, member: discord.Member):
        async with self.db.acquire() as conn:
            await conn.execute('INSERT INTO members (guild_id, user_id) VALUES ($1, $2)', member.guild.id, member.id)

    async def on_member_remove(self, member: discord.Member):
        async with self.db.acquire() as conn:
            await conn.execute('DELETE FROM members WHERE guild_id = $1 AND user_id = $2', member.guild.id, member.id)

    async def on_guild_join(self, guild: discord.Guild):
        await self.sync_guild(guild)
        log.info(f'synced state of {guild} {guild.id}')

    async def on_guild_remove(self, guild: discord.Guild):
        async with self.db.acquire() as conn:
            await conn.execute('DELETE FROM members WHERE guild_id = $1', guild.id)

    async def full_sync(self):
        await self.bot.wait_until_ready()

        log.info('starting to sync state')

        # since the connection pool has 10 connections we might as well use them
        with Timer() as timer:
            await asyncio.gather(
                *[self.sync_guild(x) for x in self.bot.guilds]
            )

        log.info(f'synced full state, took {timer}')

    async def sync_guild(self, guild: discord.Guild):
        async with self.db.acquire() as conn:

            # calculate which users left, which users are new
            results = await conn.fetch('SELECT user_id FROM members WHERE guild_id = $1', guild.id)

            new_members = []
            stale_members = []

            old = set(x['user_id'] for x in results)
            current = set(x.id for x in guild.members)

            for user_id in old.symmetric_difference(current):
                if user_id in current:
                    new_members.append((guild.id, user_id))
                else:
                    stale_members.append((guild.id, user_id))

            # insert new members, delete old ones
            await conn.executemany('INSERT INTO members (guild_id, user_id) VALUES ($1, $2)', new_members)
            await conn.executemany('DELETE FROM members WHERE guild_id = $1 AND user_id = $2', stale_members)


def setup(bot: JoseBot):
    bot.add_cog(State(bot))
