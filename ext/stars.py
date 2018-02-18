#!/usr/bin/env python3

import asyncio
import discord
import sys
import copy
sys.path.append("..")
import jauxiliar as jaux
import collections

from random import SystemRandom
random = SystemRandom()

DEFAULT_STARDB = '''{
    "locks": []
}'''

perm_overwrite = discord.PermissionOverwrite
channel_perms = discord.ChannelPermissions

BLUE    = 0x0066ff
BRONZE  = 0xc67931
SILVER  = 0xC0C0C0
GOLD    = 0xD4AF37
RED     = 0xff0000
WHITE   = 0xffffff

def _data(message, user):
    '''Extract data from message and user objects'''
    if isinstance(message, dict) and user is None:
        return message['server_id'], message['channel_id'], message['message_id']

    server_id = str(message.server.id)
    channel_id = str(message.channel.id)
    message_id = str(message.id)
    user_id = str(user.id)
    return server_id, channel_id, message_id, user_id

class Stars(jaux.Auxiliar):
    '''
    Stars - Starboard module
    '''
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)
        self.star_global_lock = False

        self.star_lock = collections.defaultdict(asyncio.Lock)

        # Clean messages with 0 stars from starboard
        #self.cbk_new('stars.cleaner', self.stars_cleaner, 1200)

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

    def is_nsfw_channel(self, channel_id):
        channel = self.client.get_channel(channel_id)
        if channel is None:
            return None

        n = channel.name
        return n == 'nsfw' if len(n) < 5 else n[:5] == 'nsfw-'

    async def stars_cleaner(self):
        '''
        stars_cleaner - checks all stars and removes messages
        with 0 stars from the database.
        '''
        for guild_id in self.stars:
            # skip locks
            if guild_id == 'locks':
                continue

            starboard = self.stars[guild_id]
            stars = starboard['stars']

            # use a copy since we delete while iterating
            for message_id in copy.copy(stars):
                star = stars[message_id]
                if len(star['starrers']) > 0:
                    continue

                guild = self.client.get_server(guild_id)
                if guild is None:
                    self.logger.info("[cleaner] autoremoving server %s", guild_id)
                    del self.stars[guild_id]
                    break

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

    def star_color(self, stars):
        color = 0xffff00
        if stars >= 0:
            color = BLUE
        if stars >= 3:
            color = BRONZE
        if stars >= 5:
            color = SILVER
        if stars >= 10:
            color = GOLD
        if stars >= 20:
            color = RED
        if stars >= 50:
            color = WHITE
        return color

    def make_embed(self, message, stars, sfw_embed=True):
        '''Creates an embed with the attachments from the message, etc'''
        content = message.content
        nsfw_channel = self.is_nsfw_channel(message.channel.id)

        em = discord.Embed(description=content, colour=self.star_color(stars))
        if nsfw_channel and sfw_embed:
            em.description = f'**[WARNING: NSFW]**\n{em.description}'

        em.timestamp = message.timestamp

        author = message.author
        avatar = author.avatar_url or author.default_avatar_url
        em.set_author(name=author.display_name, icon_url=avatar)

        attch = message.attachments
        if attch:
            attch_url = attch[0]['url']
            if attch_url.lower().endswith(('png', 'jpeg', 'jpg', 'gif')):
                if nsfw_channel and sfw_embed:
                    em.description = f'{em.description}\n[NSFW ATTACHMENT]({attch_url})'
                else:
                    em.set_image(url=attch_url)
            else:
                attachments = '[Attachment](%s)' % attch_url
                if content:
                    em.description = message.content + '\n' + attachments
                else:
                    em.description = attachments

        return em

    async def update_star(self, server_id, channel_id, message_id, delete=False):
        # Do usual checking because of sanity

        try:
            starboard = self.stars[server_id]
        except IndexError:
            raise Exception('starboard not found')

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
            star = starboard['stars'][message_id]
        except KeyError:
            raise Exception('star not found')

        # check if the starboard is sane enough
        starboard_id = starboard['starboard_id']
        starboard_channel = server.get_channel(starboard_id)
        if starboard_channel is None:
            # if the starboard channel isn't found, there is no need to maintain it.
            self.logger.info('Autoremoving %s[%s] from starboard', \
                server.name, server_id)
            del self.stars[server_id]
            raise Exception('Autoemoved %s from starboard' % server_id)

        # check star object
        stars = len(star['starrers'])
        star_msg_id = star['star_message']
        star_msg = None

        try:
            # if possible, edit the message
            if star_msg_id is not None:
                star_msg = await self.client.get_message(starboard_channel, star_msg_id)
        except discord.NotFound:
            pass

        # remove message if stars came to 0
        if stars < 1 and star_msg is not None:
            await self.client.delete_message(star_msg)
            return True

        # don't do anything if 0 stars, pls
        if stars < 1:
            return True

        m_embed = self.make_embed(message, stars)
        m_str = self.star_str(star, message)

        # edit if possible
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
        await self.star_lock[server_id]

        try:
            self.stars['locks'].index(server_id)
            self.star_lock[server_id].release()
            return False
        except ValueError:
            pass

        if user.bot:
            return

        try:
            starboard = self.stars[server_id]
        except KeyError:
            self.star_lock[server_id].release()
            return False

        if message.channel.id == starboard['starboard_id']:
            self.star_lock[server_id].release()
            return False

        # create star object if needed
        stars = starboard['stars']
        if message_id not in stars:
            starboard['stars'][message_id] = {
                'channel_id': channel_id,
                'star_message': None,
                'starrers': [],
            }

        # add star
        star = starboard['stars'][message_id]
        try:
            star['starrers'].index(user_id)
            self.star_lock[server_id].release()
            return False
        except ValueError:
            star['starrers'].append(user_id)

        try:
            done = await self.update_star(server_id, channel_id, message_id)
        except Exception as err:
            self.logger.error('add_star(%s, %s[%s])', message.id, \
                user.name, user.id, exc_info=True)
            self.star_lock[server_id].release()
            return False

        if not done:
            self.logger.error('update_star sent False')
            self.star_lock[server_id].release()
            return False

        self.star_lock[server_id].release()
        return True

    async def remove_star(self, message, user):
        if self.star_global_lock:
            return False

        server_id, channel_id, message_id, user_id = _data(message, user)
        await self.star_lock[server_id]

        try:
            self.stars['locks'].index(server_id)
            self.star_lock[server_id].release()
            return
        except ValueError:
            pass

        if user.bot:
            return

        try:
            starboard = self.stars[server_id]
        except IndexError:
            self.star_lock[server_id].release()
            return False

        if message.channel.id == starboard['starboard_id']:
            self.star_lock[server_id].release()
            return False

        star = starboard['stars'].get(message_id)
        if star is None:
            self.star_lock[server_id].release()
            return False

        try:
            star['starrers'].remove(user_id)
        except ValueError:
            self.star_lock[server_id].release()
            return False

        try:
            done = await self.update_star(server_id, channel_id, message_id)
        except:
            self.logger.error('remove_star(%s, %s[%s])', message.id, \
                user.name, user.id, exc_info=True)
            self.star_lock[server_id].release()
            return False

        if not done:
            self.logger.error('update_star sent False')
            self.star_lock[server_id].release()
            return False

        self.star_lock[server_id].release()
        return True

    async def remove_all(self, message):
        server_id, channel_id, message_id = _data(message, None)
        await self.star_lock[server_id]

        try:
            self.stars['locks'].index(server_id)
            self.star_lock[server_id].release()
            return
        except ValueError:
            pass

        try:
            starboard = self.stars[server_id]
        except IndexError:
            self.star_lock[server_id].release()
            return False

        # remove all stars from the message, also delete it
        try:
            done = await self.update_star(server_id, channel_id, \
                message_id, delete=True)
        except:
            self.star_lock[server_id].release()
            return False

        if not done:
            self.logger.error('update_star sent False')
            self.star_lock[server_id].release()
            return False

        try:
            self.logger.info("Removing message:%s from starboard:%s", \
                message_id, server_id)
            del starboard['stars'][message_id]
        except IndexError:
            self.star_lock[server_id].release()
            return False

        self.star_lock[server_id].release()
        return True

    async def e_reaction_add(self, reaction, user):
        if reaction.custom_emoji:
            return

        if reaction.emoji != '⭐':
            return

        m = reaction.message
        res = await self.add_star(m, user)
        if not res:
            self.logger.warning('[add_star] Failed to add star to %s@%s, %s[%s]', \
                m.id, m.server.id, user.name, user.id)

    async def e_reaction_remove(self, reaction, user):
        if reaction.custom_emoji:
            return

        if reaction.emoji != '⭐':
            return

        m = reaction.message
        res = await self.remove_star(m, user)
        if not res:
            self.logger.warning('[remove_star] Failed to Remove star to %s@%s, %s[%s]', \
                m.id, m.server.id, user.name, user.id)

    async def e_reaction_clear(self, message, reactions):
        starboard = self.stars.get(str(message.server.id))
        if starboard is None:
            return

        if str(message.id) not in starboard['stars']:
            return

        res = await self.remove_all(message)
        if not res:
            self.logger.warning("[remove_all] Failed to remove all stars,  %s@%s", \
                message.id, message.server.id)

    async def c_starboard(self, message, args, cxt):
        '''`j!starboard channel_name` - initialize Starboard'''

        try:
            starboard_name = args[1]
        except:
            await cxt.say("Error parsing channel name")
            return

        server = message.server

        if server.id in self.stars:
            await cxt.say("dude you can't create 2 starboards")
            return

        self.logger.info('[stars] Initializing starboard @ %s[%s]', \
            str(message.server.name), message.server.id)

        # everyone can read, only jose can write
        everyone_perms = perm_overwrite(read_messages=True, send_messages=False)
        jose_perms = perm_overwrite(read_messages=True, send_messages=True)

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
            await cxt.say(":ok_hand: Starboard initialized! Make sure only josé can send messages on the channel(*psst* `j!helpme` if you have issues).")
        else:
            await cxt.say(":sob: Starboard initialization failed :sob:")

    async def c_star(self, message, args, cxt):
        '''`j!star message_id` - :star: stars a message in the current channel'''
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

    async def c_unstar(self, message, args, cxt):
        '''`j!unstar message_id` - :hole: unstars a message in the current channel'''
        try:
            message_id = args[1]
        except:
            await cxt.say("Error parsing Message ID.")
            return

        try:
            to_unstar = await self.client.get_message(message.channel, message_id)
        except discord.NotFound:
            await cxt.say("Message not found in this channel.")
        except discord.Forbidden:
            await cxt.say("No permissions to get messages")
        except discord.HTTPException:
            await cxt.say("Failed to retreive the message")
        else:
            res = await self.remove_star(to_unstar, message.author)
            if not res:
                await cxt.say("Error unstarring message.")
            else:
                await cxt.say("rip.")

    async def c_starlock(self, message, args, cxt):
        '''`j!starlock <op> [server_id]` - lock a server's starboard or lock globally'''
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
            try:
                server_id = args[2]
                server = self.client.get_server(server_id)
            except IndexError:
                server = message.server
                server_id = str(server.id)

            if server is None:
                await cxt.say("Server not found")
                return

            try:
                self.stars['locks'].index(server_id)
                self.stars['locks'].remove(server_id)
                await cxt.say(":unlock: Removed lock for %s[%s]", \
                    (server.name, server_id))
            except ValueError:
                self.stars['locks'].append(server_id)
                await cxt.say(":lock: Locked starboard for %s[%s]", \
                    (server.name, server_id))
        else:
            await cxt.say("Operation not found")

    async def c_starrers(self, message, args, cxt):
        '''`j!starrers message_id` - list all people who starred a message'''
        try:
            message_id = args[1]
        except:
            await cxt.say("Error parsing Message ID.")
            return

        try:
            msg = await self.client.get_message(message.channel, message_id)
        except discord.NotFound:
            await cxt.say("Message not found in this channel.")
        except discord.Forbidden:
            await cxt.say("No permissions to get messages")
        except discord.HTTPException:
            await cxt.say("Failed to retreive the message")
        else:
            server_id, _, _, _ = _data(message, message.author)

            try:
                starboard = self.stars[server_id]
            except IndexError:
                await cxt.say("No starboard initialized")
                return

            if message.channel.id == starboard['starboard_id']:
                await cxt.say('lol no')
                return False

            star = starboard['stars'].get(message_id)
            if star is None:
                await cxt.say(f'message {message_id} not found in starboard: `{star}`')
                return False

            em = self.make_embed(msg, len(star['starrers']), False)

            starrers_as_members = [discord.utils.get(self.client.get_all_members(), \
                id=mid, server__id=server_id) for mid in star['starrers']]

            em.add_field(name='Starrers', value=', '.join([m.display_name \
                for m in starrers_as_members]))

            try:
                await cxt.say_embed(em)
            except Exception as err:
                await cxt.say(":sob: `{err!r}`")

    async def c_randomstar(self, message, args, cxt):
        '''`j!randomstar` - shows random star :thinking:'''
        server_id, _, _, _ = _data(message, message.author)

        in_nsfw = self.is_nsfw_channel(message.channel.id)

        try:
            starboard = self.stars[server_id]
        except KeyError:
            await cxt.say("No starboard initialized")
            return

        stars = starboard['stars']
        msg_channel = None
        tries = 0
        while msg_channel is None:
            if tries > 20:
                await cxt.say("Tried 20 rerolls, didn't find anything")
                return

            message_id = random.choice(list(stars.keys()))
            star = stars.get(message_id)
            if star is None:
                await cxt.say(f'LOL I CHOSE A NONEXISTING MESSAGE')
                return

            msg_channel = self.client.get_channel(star['channel_id'])
            if msg_channel is not None:
                is_nsfw = self.is_nsfw_channel(msg_channel.id)

                # if you run j!rs from NSFW channel, only stars from NSFW
                # channel will appear. same for SFW channels
                if in_nsfw != is_nsfw:
                    msg_channel = None
            tries += 1

        try:
            msg = await self.client.get_message(msg_channel, message_id)
        except discord.NotFound:
            await cxt.say("Message not found in this channel.")
            return
        except discord.Forbidden:
            await cxt.say("No permissions to get messages")
            return
        except discord.HTTPException:
            await cxt.say("Failed to retreive the message")
            return

        # make the embed same way it would be on starboard channel
        em = self.make_embed(msg, len(star['starrers']), False)
        m_str = self.star_str(star, msg)
        await self.client.send_message(message.channel, m_str, embed=em)

    async def c_rs(self, message, args, cxt):
        '''`j!rs` - alias for `j!randomstar`'''
        await self.c_randomstar(message, args, cxt)

    async def c_starstats(self, message, args, cxt):
        '''`j!starstats` - Get statistics about your starboard'''
        server_id, _, _, _ = _data(message, message.author)

        try:
            starboard = self.stars[server_id]
        except IndexError:
            await cxt.say("No starboard initialized")
            return

        stars = starboard['stars']

        if len(stars.keys()) < 1:
            await cxt.say("how can I show statistics if there isn't anything starred to start with?")
            return

        stats = discord.Embed(title="Starboard statistics", colour=discord.Colour(0xFFFF00))

        # thats dumb, but needed
        starrers = collections.Counter()
        max_message = [0, None]
        for message_id in stars:
            star = stars[message_id]
            _starrers = star['starrers']
            if len(_starrers) > max_message[0]:
                max_message = [len(_starrers), message_id, star]

            for starrer_id in star['starrers']:
                starrers[starrer_id] += 1

        top10_starrers = starrers.most_common(3)

        _members = [(discord.utils.get(self.client.get_all_members(), id=mid, server__id=server_id), n_stars) for (mid, n_stars) in top10_starrers]

        stats.add_field(name='Most stars received',
                        value=f'{max_message[0]} Stars, ID {max_message[1]} on <#{max_message[2]["channel_id"]}>')

        stats.add_field(name='Starrer #1',
                        value=f'{_members[0][0].mention} with {_members[0][1]}')
        stats.add_field(name='Starrer #2',
                        value=f'{_members[1][0].mention} with {_members[1][1]}')
        stats.add_field(name='Starrer #3',
                        value=f'{_members[2][0].mention} with {_members[2][1]}')

        await cxt.say_embed(stats)

    async def c_restore(self, message, args, cxt):
        '''
        `j!restore` - good luck

        This should only be used in the case of a catastrophic failure
        where the starboard channel is deleted.
        '''
        await self.is_admin(message.author.id)
        await cxt.say("This will take.... time")

        server_id, _, _, _ = _data(message, message.author)

        try:
            starboard = self.stars[server_id]
        except IndexError:
            await cxt.say("No starboard initialized")
            return

        done = 0
        tot = 0
        stars = starboard['stars']

        for message_id in list(stars.keys()).sort():
            star = stars[message_id]
            try:
                stat = await self.update_star(server_id, star['channel_id'], message_id)
            except:
                stat = False

            if stat:
                done += 1
            tot += 1

        await cxt.say(f"Restored {done}/{tot} messages")
