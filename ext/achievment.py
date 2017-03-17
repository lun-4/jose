#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import jauxiliar as jaux
import joseerror as je

ACHIEVMENT_NAMES = {
    '5-meme': 'Made 5 memes in `j!meme`',
    '10-meme': 'Made 10 memes in `j!meme`',
}

ACHIEVMENT_EMOJI = {
    '5-meme':   '<:thunking:286955648472711168>',
    '10-meme':  '<:thonking:260597447858978816>',
}

ACHIEVMENT_OVERWRITES = {
    '10-meme': ('5-meme',),
}

class JoseAchievment(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)

        self.jsondb('achievments', path='db/achievments.json')

    async def ext_load(self):
        try:
            return True, ''
        except Exception as err:
            return False, repr(err)

    async def ext_unload(self):
        try:
            return True, ''
        except Exception as err:
            return False, repr(err)

    def mk_achievment(self, achievment_id):
        achv_description = ACHIEVMENTS[achievment_id]
        achv_emoji = ACHIEVMENT_EMOJI[achievment_id]

        return {
            'id': achievment_id,
            'description': achv_description,
            'emoji': achv_emoji,
        }

    def achv_ensure(self, userid):
        user = self.achievments.get(userid, None)
        # create shit
        if user is None:
            self.achievments[userid] = {}

    def achv_get(self, userid):
        userid = str(userid)

        self.achv_ensure(userid)
        return self.achievments.get(userid)

    def achv_add(self, user_id, achievment_id):
        if achievment_id not in ACHIEVMENT_NAMES:
            return False

        user_id = str(user_id)

        achievments = self.achv_get(user_id)

        if achievment_id in achievments:
            return True

        overwrites = ACHIEVMENT_OVERWRITES.get(achievment_id, {})
        for conflict in overwrites:
            achievments.remove(conflict)

        # add the shit
        achievments.append(overwrites)
        self.logger.info("Add achievment %r to %s", achievment_id, user)
        return True

    async def c_achievments(self, message, args, cxt):
        achievments = self.achv_get(str(message.author.id))
        emoji = [ACHIEVMENT_EMOJI[a] for a in achievments]
        await cxt.say(' '.join(emoji))

    async def c_listachv(self, message, args, cxt):
        await self.is_admin(message.author.id)
        res = ['`{}` - {}\n'.format(k, ACHIEVMENT_NAMES[k]) for (k) in ACHIEVMENT_NAMES]
        await cxt.say("%s", ('\n'.join(res),))

    async def c_addachv(self, message, args, cxt):
        await self.is_admin(message.author.id)

        try:
            user_id = await jcommon.parse_id(args[1])
            achievment_id = args[2]
        except:
            await cxt.say("error parsing shit")
            return

        if user_id is None:
            await cxt.say("error parsing shit")
            return

        result = self.achv_add(user_id, achievment_id)
        if not result:
            await cxt.say("Error adding achievment `%s` to userid %s", \
                (achievment_id, user_id))
        else:
            await cxt.say("Now %s has `%s`", \
                (user_id, self.achv_get(user_id)))

        await self.json_save('achievments')
