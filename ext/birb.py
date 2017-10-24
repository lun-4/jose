import joseconfig
import twitter

import discord
from discord.ext import commands

from .common import Cog, shell


# Heating-proof 
censored_words = [
    "#blacklivesmatter",
    "#marchagainsttrump",
    "#gaypride",
    "hitler",
    "jew",
    "black",
    "impure",
    "purity",
    "aryan",
    "gas the"
]


class Birb(Cog):
    """Twitter cog"""
    def __init__(self, bot):
        super().__init__(bot)
        self.twitter = twitter.Api(consumer_key=bot.config.twitter_consumer_key,
                                   consumer_secret=bot.config.twitter_consumer_secret,
                                   access_token_key=bot.config.twitter_access_token_key,
                                   access_token_secret=bot.config.twitter_access_token_secret)

    @commands.command()
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def tweet(self, ctx, *, content: commands.clean_content):
        """Send a tweet."""
        if len(content) > 140:
            return await ctx.send('2 long')
        for word in censored_words:
            if word in content.lower():
                return await ctx.send('no >:(((')
        status = self.twitter.PostUpdate(content)
        await ctx.send(f'posted https://twitter.com/{status.user.screen_name}/status/{status.id}')

def setup(bot):
    bot.add_cog(Birb(bot))
