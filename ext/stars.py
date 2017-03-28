#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import jauxiliar as jaux
import joseerror as je

perm_overwrite = discord.PermissionOverwrite
channel_perms = discord.ChannelPermissions

class JoseExtension(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)

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

    async def add_star(self, message_id, user_id):
        pass

    async def remove_star(self, message_id, user_id):
        pass

    async def remove_all(self, message_id):
        pass

    async def e_reaction_add(self, reaction, user):
        await self.add_star(reaction.message.id, user.id)

    async def e_reaction_remove(self, reaction, user):
        await self.remove_star(reaction.message.id, user.id)

    async def e_reaction_clear(self, message, reactions):
        await self.remove_all(message.id)

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
            await self.add_star(message.id, message.author.id)
