#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import jauxiliar as jaux
import joseerror as je

perm_overwrite = discord.PermissionOverwrite
channel_perms = discord.ChannelPermissions

def _data(message, user):
    server_id = str(message.server.id)
    channel_id = str(message.channel.id)
    message_id = str(message.id)
    user_id = str(user.id)
    return server_id, channel_id, message_id, user_id

class JoseExtension(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)
        self.star_lock = False
        self.cbk_new('stars.cleaner', self.stars_cleaner, 1200)

    async def ext_load(self):
        try:
            self.jsondb('stars', path='db/stars.json')
            return True, ''
        except Exception as err:
            return False, repr(err)

    async def ext_unload(self):
        try:
            self.jsondb_save('stars')
            return True, ''
        except Exception as err:
            return False, repr(err)

    async def stars_cleaner(self):
        for guild_id in self.stars:
            starboard = self.stars[guild_id]
            stars = starboard['stars']

            for message_id in stars:
                star = stars[message_id]
                if len(star['starrers']) < 1:
                    await self.remove_all(star['message_id'])

    async def init_starboard(self, server_id, channel_id):
        server_id = str(server_id)
        channel_id = str(channel_id)

        # guild_id => starboard object
        self.stars[guild_id] = {
            'channelid': channel_id,
            # message_id => star object
            'stars': {},
        }

        self.jsondb_save('stars')

    async def update_star(self, message_id):
        # TODO: check different data and edit message accordingly
        pass

    async def add_star(self, message, user):
        if self.star_lock:
            return False

        server_id, channel_id, message_id, user_id = _data(message, user)

        try:
            starboard = self.stars[server_id]
        except IndexError:
            return False

        stars = starboard['stars']
        star = starboard['stars'].get(message_id, {
            'channel_id': channel_id,
            'starrers': [],
        })

        try:
            star['starrers'][user_id]
        except IndexError:
            star['starrers'].append(user_id)

        await self.update_star(self, message_id)
        return True

    async def remove_star(self, message, user):
        if self.star_lock:
            return False

        server_id, channel_id, message_id, user_id = _data(message, user)
        try:
            starboard = self.stars[server_id]
        except IndexError:
            return False

        stars = starboard['stars']
        star = starboard['stars'].get(message_id)
        star['starrers'].remove(user_id)

        await self.update_star(server_id, channel_id, message_id)
        return True

    async def remove_all(self, message):
        server_id = data['server']
        channel_id = data['channel']
        message_id = data['message']
        user_id = data['user']

        try:
            starboard = self.stars[server_id]
        except IndexError:
            return False

        try:
            await self.update_star(server_id, channel_id, message_id, delete=True)
        except:
            return False

        try:
            del starboard['stars'][message_id]
        except IndexError:
            return False

        return True

    async def e_reaction_add(self, reaction, user):
        if reaction.custom_emoji:
            return

        if reaction.emoji != '⭐':
            return

        m = reaction.message
        await self.add_star({
            'server': m.server.id,
            'channel': m.channel.id,
            'message' m.id,
            'user': user.id,
        })

    async def e_reaction_remove(self, reaction, user):
        if reaction.custom_emoji:
            return

        if reaction.emoji != '⭐':
            return

        m = reaction.message
        await self.remove_star({
            'server': m.server.id,
            'channel': m.channel.id,
            'message' m.id,
            'user': user.id,
        })

    async def e_reaction_clear(self, message, reactions):
        starboard = self.stars.get(str(message.server.id))
        if starboard is None:
            return

        if str(message.id) not in starboard['stars']:
            return

        await self.remove_all({
            'server': message.server.id,
            'channel': message.channel.id,
            'message': message.id,
        })

    async def c_starboard(self, message, args, cxt):
        '''`j!starboard channel_name` - initialize Starboard'''
        await self.is_admin(message.author.id)

        try:
            starboard_name = args[1]
        except:
            await cxt.say("Error parsing channel name")
            return

        server = message.server

        # everyone can read, only jose can write
        everyone_perms = perm_overwrite(read_messages=True, write_messages=False)
        jose_perms = perm_overwrite(read_messages=True, write_messages=True)

        everyone = channel_perms(target=server.default_role, overwrite=everyone_perms)
        jose = channel_perms(target=server.me, overwrite=jose_perms)

        try:
            starboard = await self.client.create_channel(server, \
                starboard_name, everyone, jose)
        except discord.Forbidden:
            await cxt.say("Forbidden to create channels.")
            return

        await self.init_starboard(self, message.server.id, starboard.id)

    async def c_star(self, message, args, cxt):
        try:
            message_id = args[1]
        except:
            await cxt.say("Error parsing Message ID.")
            return

        try:
            message = await self.client.get_message(message.channel, message_id)
        except discord.NotFound:
            await cxt.say("Message not found in this channel.")
        except discord.Forbidden:
            await cxt.say("No permissions to get messages")
        except discrord.HTTPException:
            await cxt.say("Failed to retreive the message")
        else:
            res = await self.add_star(message.id, message.author.id)
            if not res:
                await cxt.say("Error adding star to the message.")
            else:
                await cxt.say(":star: :ok_hand:")

    async def c_starlock(self, message, args, cxt):
        self.star_lock = not self.star_lock
        await cxt.say("`star_lock` set to %r" % self.star_lock)
