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
            'starboard_id': channel_id,
            # message_id => star object
            'stars': {},
        }

        self.jsondb_save('stars')

    def star_str(self, star, message):
        return '%d stars, ID: %s' % (len(star['starrers']), message.id)

    def make_embed(self, message):
        content = message.content

        em = discord.Embed(description=content, colour=discord.Colour(0xffff00))
        em.timestamp = message.timestamp
        em.set_author(message.author)

        author = message.author
        avatar = author.avatar_url or author.default_avatar_url
        em.set_author(name=author.display_name, icon_url=avatar)

        attch = message.attachments
        if attch:
            attch_url = attch[0]['url']
            if attch_url.lower().endswith(('png', 'jpeg', 'jpg', 'gif')):
                e.set_image(url=attch_url)
            else:
                attachments = '[Attachment](%s)' % attch_url
                if content:
                    em.description = message.content + '\n' + attachments
                else:
                    em.description = attachments

        return em

    async def update_star(self, server_id, channel_id, message_id, delete=False):
        server = self.client.get_server(server_id)
        if server is None:
            self.logger.warning("Server %s not found", server_id)
            raise Exception('server not found', server_id)

        channel = server.get_channel(channel_id)
        if channel is None:
            self.logger.warning('channel %s not found', channel_id)
            raise Exception('channel not found', server_id)

        try:
            message = await self.client.get_message(channel, message_id)
        except discord.NotFound:
            raise Exception('message not found')

        try:
            starboard = self.stars[server_id]
        except:
            raise Exception('starboard not found')

        try:
            star = starboard['stars'][message_id]
        except:
            raise Exception('star not found')

        starboard_id = starboard['starboard_id']
        starboard_channel = server.get_channel(starboard_id)
        if starboard_channel is None:
            del self.stars[server_id]
            self.logger.info('Autoremoving %s[%s] from starboard', \
                server.name, server_id)
            raise Exception('Autoemoved %s from starboard')

        stars = len(star['starrers'])
        star_msg_id = star['star_message']

        try:
            star_msg = await self.client.get_message(starboard_channel, star_msg_id)
        except discord.NotFound:
            star_msg = None

        m_embed = self.make_embed(message)
        m_str = self.star_str(star, message)

        if star_msg:
            await client.edit_message(star_msg, m_str, embed=m_embed)
        else:
            star_msg = await client.send_message(starboard_channel, m_str, embed=m_embed)
            star['star_message'] = str(star_msg.id)

        self.jsondb_save('stars')

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
            'star_message': None,
            'starrers': [],
        })

        try:
            star['starrers'][user_id]
        except IndexError:
            star['starrers'].append(user_id)

        try:
            await self.update_star(server_id, channel_id, message_id)
        except:
            return False

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

        try:
            await self.update_star(server_id, channel_id, message_id)
        except:
            return False

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
