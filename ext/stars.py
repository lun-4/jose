#!/usr/bin/env python3

import discord
import sys
import copy
sys.path.append("..")
import jauxiliar as jaux

DEFAULT_STARDB = '''{
    "locks": []
}'''

perm_overwrite = discord.PermissionOverwrite
channel_perms = discord.ChannelPermissions

def _data(message, user):
    if isinstance(message, dict) and user is None:
        return message['server_id'], message['channel_id'], message['message_id']

    server_id = str(message.server.id)
    channel_id = str(message.channel.id)
    message_id = str(message.id)
    user_id = str(user.id)
    return server_id, channel_id, message_id, user_id

class Stars(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)
        self.star_global_lock = False
        self.cbk_new('stars.cleaner', self.stars_cleaner, 1200)

    async def ext_load(self):
        try:
            self.jsondb('stars', path='db/stars.json', default=DEFAULT_STARDB)
            if 'locks' not in self.stars:
                self.stars['locks'] = []

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
            # skip locks
            if guild_id == 'locks':
                continue

            starboard = self.stars[guild_id]
            stars = starboard['stars']

            c_stars = copy.copy(stars)
            for message_id in c_stars:
                star = stars[message_id]
                if len(star['starrers']) > 0:
                    continue

                guild = self.client.get_server(guild_id)
                if guild is None:
                    self.logger.info("[starboard] autoremoving server %s", guild_id)
                    del self.stars[guild_id]
                    return

                channel = guild.get_channel(star['channel_id'])
                if channel is None:
                    continue
                try:
                    await self.client.get_message(channel, message_id)
                except discord.NotFound:
                    self.logger.warning("[cleaner:NotFound] removing message:%s from starboard:%s", \
                        message_id, guild_id)
                    del stars[message_id]
                    continue

                await self.remove_all({
                    'server_id': guild_id,
                    'channel_id': star['channel_id'],
                    'message_id': message_id
                })

    async def init_starboard(self, server_id, channel_id):
        server_id = str(server_id)
        channel_id = str(channel_id)

        # guild_id => starboard object
        if server_id in self.stars:
            return False

        self.stars[server_id] = {
            'starboard_id': channel_id,
            # message_id => star object
            'stars': {},
        }

        self.jsondb_save('stars')
        return True

    def star_str(self, star, message):
        return '%d stars, <#%s> ID: %s' % \
            (len(star['starrers']), message.channel.id, message.id)

    def make_embed(self, message):
        content = message.content

        em = discord.Embed(description=content, colour=discord.Colour(0xffff00))
        em.timestamp = message.timestamp

        author = message.author
        avatar = author.avatar_url or author.default_avatar_url
        em.set_author(name=author.display_name, icon_url=avatar)

        attch = message.attachments
        if attch:
            attch_url = attch[0]['url']
            if attch_url.lower().endswith(('png', 'jpeg', 'jpg', 'gif')):
                em.set_image(url=attch_url)
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
        except IndexError:
            raise Exception('starboard not found')

        try:
            star = starboard['stars'][message_id]
        except KeyError:
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
        star_msg = None

        try:
            if star_msg_id is not None:
                star_msg = await self.client.get_message(starboard_channel, star_msg_id)
        except discord.NotFound:
            pass

        if stars < 1 and star_msg is not None:
            await self.client.delete_message(star_msg)
            return True

        if stars < 1:
            return True

        m_embed = self.make_embed(message)
        m_str = self.star_str(star, message)

        if star_msg is not None:
            await self.client.edit_message(star_msg, \
                m_str, embed=m_embed)
        else:
            star_msg = await self.client.send_message(starboard_channel, \
                m_str, embed=m_embed)
            star['star_message'] = str(star_msg.id)

        self.jsondb_save('stars')
        return True

    async def add_star(self, message, user):
        if self.star_global_lock:
            return False

        server_id, channel_id, message_id, user_id = _data(message, user)

        try:
            self.stars['locks'].index(server_id)
            return
        except ValueError:
            pass

        try:
            starboard = self.stars[server_id]
        except KeyError:
            return False

        if message.channel.id == starboard['starboard_id']:
            return False

        stars = starboard['stars']
        if message_id not in stars:
            starboard['stars'][message_id] = {
                'channel_id': channel_id,
                'star_message': None,
                'starrers': [],
            }

        star = starboard['stars'][message_id]

        try:
            star['starrers'].index(user_id)
            return False
        except ValueError:
            star['starrers'].append(user_id)

        try:
            done = await self.update_star(server_id, channel_id, message_id)
        except:
            self.logger.error('add_star(%s, %s[%s])', message.id, \
                user.name, user.id, exc_info=True)
            return False

        if not done:
            self.logger.error('update_star sent False')
            return False

        return True

    async def remove_star(self, message, user):
        if self.star_global_lock:
            return False

        server_id, channel_id, message_id, user_id = _data(message, user)

        try:
            self.stars['locks'].index(server_id)
            return
        except ValueError:
            pass

        try:
            starboard = self.stars[server_id]
        except IndexError:
            return False

        if message.channel.id == starboard['starboard_id']:
            return False

        star = starboard['stars'].get(message_id)
        if star is None:
            return False

        try:
            star['starrers'].remove(user_id)
        except ValueError:
            return False

        try:
            done = await self.update_star(server_id, channel_id, message_id)
        except:
            self.logger.error('remove_star(%s, %s[%s])', message.id, \
                user.name, user.id, exc_info=True)
            return False

        if not done:
            self.logger.error('update_star sent False')
            return False

        return True

    async def remove_all(self, message):
        server_id, channel_id, message_id = _data(message, None)

        try:
            self.stars['locks'].index(server_id)
            return
        except ValueError:
            pass

        try:
            starboard = self.stars[server_id]
        except IndexError:
            return False

        try:
            done = await self.update_star(server_id, channel_id, \
                message_id, delete=True)
        except:
            return False

        if not done:
            self.logger.error('update_star sent False')
            return False

        try:
            self.logger.info("Removing message:%s from starboard:%s:%r", \
                message_id, server_id, message.server.name)
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
        await self.add_star(m, user)

    async def e_reaction_remove(self, reaction, user):
        if reaction.custom_emoji:
            return

        if reaction.emoji != '⭐':
            return

        m = reaction.message
        await self.remove_star(m, user)

    async def e_reaction_clear(self, message, reactions):
        starboard = self.stars.get(str(message.server.id))
        if starboard is None:
            return

        if str(message.id) not in starboard['stars']:
            return

        await self.remove_all(message)

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

        res = await self.init_starboard(message.server.id, starboard.id)
        if res:
            await cxt.say(":ok_hand: Starboard initialized :ok_hand:")
        else:
            await cxt.say(":sob: Starboard initialization failed :sob:")

    async def c_star(self, message, args, cxt):
        try:
            message_id = args[1]
        except:
            await cxt.say("Error parsing Message ID.")
            return

        try:
            to_star = await self.client.get_message(message.channel, message_id)
        except discord.NotFound:
            await cxt.say("Message not found in this channel.")
        except discord.Forbidden:
            await cxt.say("No permissions to get messages")
        except discord.HTTPException:
            await cxt.say("Failed to retreive the message")
        else:
            res = await self.add_star(to_star, message.author)
            if not res:
                await cxt.say("Error adding star to the message.(probably starring twice?)")
            else:
                await cxt.say(":star: :ok_hand:")

    async def c_starlock(self, message, args, cxt):
        await self.is_admin(message.author.id)

        try:
            operation = args[1]
        except:
            await cxt.say("Error parsing `operation`")
            return

        if operation == 'global':
            self.star_global_lock = not self.star_global_lock
            await cxt.say("`star_global_lock` set to %r" % self.star_global_lock)
        elif operation == 'local':
            server_id = str(message.server.id)
            try:
                self.stars['locks'].index(server_id)
                self.stars['locks'].remove(server_id)
                await cxt.say("Removed lock for %s[%s]", (message.server.name, server_id))
            except ValueError:
                self.stars['locks'].append(str(message.server.id))
                await cxt.say(":lock: Locked starboard for %s[%s]", (message.server.name, server_id))
        else:
            await cxt.say("Operation not found")
