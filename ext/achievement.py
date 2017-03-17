#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import jauxiliar as jaux
import joseerror as je
import josecommon as jcommon

ACHIEVEMENT_NAMES = {
    '5-meme': 'Made 5 memes in `j!meme`',
    '10-meme': 'Made 10 memes in `j!meme`',
}

ACHIEVEMENT_EMOJI = {
    '5-meme':   '<:thunking:286955648472711168>',
    '10-meme':  '<:thonking:260597447858978816>',
}

ACHIEVEMENT_OVERWRITES = {
    '10-meme': ('5-meme',),
}

class JoseAchievement(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)

        self.jsondb('achievements', path='db/achievements.json')

    async def ext_load(self):
        try:
            return True, ''
        except Exception as err:
            return False, repr(err)

    async def ext_unload(self):
        try:
            await self.jsondb_save_all()
            return True, ''
        except Exception as err:
            return False, repr(err)

    def mk_achievment(self, achievement_id):
        achv_description = ACHIEVEMENTS[achievement_id]
        achv_emoji = ACHIEVEMENT_EMOJI[achievement_id]

        return {
            'id': achievEment_id,
            'description': achv_description,
            'emoji': achv_emoji,
        }

    def achv_ensure(self, userid):
        user = self.achievements.get(userid, None)
        # create shit
        if user is None:
            self.achievements[userid] = []

    def achv_get(self, userid):
        userid = str(userid)

        self.achv_ensure(userid)
        return self.achievements.get(userid)

    def achv_add(self, user_id, achievement_id):
        if achievement_id not in ACHIEVEMENT_NAMES:
            return False

        user_id = str(user_id)

        achievements = self.achv_get(user_id)

        if achievement_id in achievements:
            return True

        overwrites = ACHIEVEMENT_OVERWRITES.get(achievement_id, {})
        for conflict in overwrites:
            achievements.remove(conflict)

        # add the shit
        achievements.append(achievement_id)
        self.logger.info("Add achievement %r to %s", achievEment_id, user_id)
        return True

    async def c_achievements(self, message, args, cxt):
        achievements = self.achv_get(str(message.author.id))
        emojis = [ACHIEVEMENT_EMOJI[a] for a in achievements]

        em = discord.Embed(title='Your achievements', colour=discord.Colour.dark_teal())
        if len(emojis) > 0:
            em.add_field(name='stuff', value=' '.join(emojis))
        else:
            em.add_field(name='No achievments', value='rip')

        await cxt.say_embed(em)

    async def c_listachv(self, message, args, cxt):
        await self.is_admin(message.author.id)
        res = ['`{}` - {}\n'.format(k, ACHIEVEMENT_NAMES[k]) for (k) in ACHIEVEMENT_NAMES]
        await cxt.say("%s", ('\n'.join(res),))

    async def c_addachv(self, message, args, cxt):
        await self.is_admin(message.author.id)

        try:
            user_id = await jcommon.parse_id(args[1])
        except Exception as err:
            await cxt.say("error parsing `user_id` %r", (err,))
            return

        try:
            achievement_id = args[2]
        except:
            await cxt.say("error parsing `achievement_id`")
            return

        if user_id is None:
            await cxt.say("error parsing shit(user_id)")
            return

        result = self.achv_add(user_id, achievement_id)

        if not result:
            await cxt.say("Error adding achievement `%s` to userid %s", \
                (achievement_id, user_id))
        else:
            await cxt.say("Now <@%s> has `%s`", \
                (user_id, self.achv_get(user_id)))

        self.jsondb_save('achievements')
