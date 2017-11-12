import logging
import math

import discord

from discord.ext import commands

from .common import Cog

log = logging.getLogger(__name__)
LEVEL_CONSTANT = 0.24


ITEMS = {

}

SKILLS = {
}

SHOPS = {
}

QUESTS = {
}


class RPG(Cog):
    """RPG module."""
    def __init__(self, bot):
        super().__init__(bot)

        # All users are here, with their items and skills
        self.inventory_coll = self.config.jose_db['rpg_inventory']

    def get_level(self, inv) -> int:
        return int(LEVEL_CONSTANT * math.sqrt(inv['xp']))

    def get_next_level_xp(self, inv) -> int:
        """Gives how many XP is required to the next level."""
        lvl = self.get_level(inv)

        # level = C * sqrt(xp)
        # sqrt(xp) = level / C
        # xp = (level / C) ^ 2
        return int(pow((lvl + 1) / LEVEL_CONSTANT, 2))

    async def get_inventory(self, user_id: int) -> dict:
        return await self.inventory_coll.find_one({'user_id': user_id})

    @commands.group()
    async def rpg(self, ctx):
        """Main entry command to José RPG."""
        pass

    @rpg.command()
    async def enter(self, ctx):
        """Enter RPG.

        You cannot leave.
        """

        if await self.get_inventory(ctx.author.id):
            return await ctx.send('You already have a RPG profile')

        await self.inventory_coll.insert_one({
            'user_id': ctx.author.id,
            'xp': 0,

            # dict: int (item id) -> int (count)
            'items': {},

            # dict: int (skill id) -> int (skill level)
            'skills': {},

            # quest ID: int
            'current_quest': None,

            # TODO: those
            'equiped_weapon': None,
            'equiped_armor': None,
        })

        await ctx.ok()

    @rpg.command(name='inventory', aliases=['inv'])
    async def inventory(self, ctx, person: discord.User = None):
        """See your inventory."""
        if not person:
            person = ctx.author

        inv = await self.get_inventory(person.id)
        if not inv:
            return await ctx.send('No inventory found')

        e = discord.Embed(title=f'Inventory for {person}')

        if len(person.avatar_url):
            e.set_thumbnail(url=person.avatar_url)

        # calculate XP and levels
        e.add_field(name='Level',
                    value=str(self.get_level(inv)))

        xp_next_level = self.get_next_level_xp(inv)
        e.add_field(name='XP',
                    value=f'{inv["xp"]} / {xp_next_level} XP')

        amount = (await self.jcoin.get_account(person.id))['amount']
        e.add_field(name='Money',
                    value=f'{amount}JC')

        # items
        e.add_field(name='Items',
                    value='\u200b' + '\n'.join(
                        f'`{name}` - {count}' for (name, count)
                        in inv['items'].items()))

        await ctx.send(embed=e)

    @rpg.group()
    async def shop(self, ctx):
        pass

    @shop.command()
    async def view(self, ctx):
        """Check available items in the shop"""
        pass

    @shop.command()
    async def buy(self, ctx, item):
        """Buy an item from the shop."""
        pass


def setup(bot):
    bot.add_cog(RPG(bot))
