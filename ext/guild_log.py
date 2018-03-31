import logging
import asyncio

import discord

from .common import Cog


class GuildLog(Cog):
    def __init__(self, bot):
        super().__init__(bot)
        wbh = discord.Webhook.from_url
        adp = discord.AsyncWebhookAdapter(self.bot.session)

        self.webhook = wbh(self.bot.config.GUILD_LOGGING, adapter=adp)

    def guild_embed(self, em, guild):
        em.set_thumbnail(url=guild.icon_url)

        em.add_field(name='guild id', value=guild.id)

        em.add_field(name='guild name', value=guild.name)
        em.add_field(name='guild owner', value=guild.owner)
        em.add_field(name='guild region', value=str(guild.region))
        em.add_field(name='guild member count', value=guild.member_count)
        em.add_field(name='guild large?', value=guild.large)
        em.add_field(name='guild <- shard id', value=guild.shard_id)

    async def on_guild_join(self, guild):
        if not self.bot.is_ready():
            return

        em = discord.Embed(title='Guild join', color=discord.Color.green())
        self.guild_embed(em, guild)
        await self.webhook.execute(embed=em)

    async def on_guild_remove(self, guild):
        if not self.bot.is_ready():
            return

        em = discord.Embed(title='Guild remove', color=discord.Color.red())
        self.guild_embed(em, guild)
        await self.webhook.execute(embed=em)

    async def on_guild_unavailable(self, guild):
        if not self.bot.is_ready():
            return

        em = discord.Embed(
            title='Guild unavailable', color=discord.Color(0xfcd15c))

        self.guild_embed(em, guild)
        await self.webhook.execute(embed=em)

    async def on_guild_available(self, guild):
        if not self.bot.is_ready():
            return

        em = discord.Embed(
            title='Guild available', color=discord.Color(0x00f00f))

        self.guild_embed(em, guild)
        await self.webhook.execute(embed=em)


def setup(bot):
    bot.add_cog(GuildLog(bot))
