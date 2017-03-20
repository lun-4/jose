#!/usr/bin/env python3

import discord
import sys
sys.path.append("..")
import jauxiliar as jaux
import joseerror as je
import josecommon as jcommon
import uuid
import time
import copy

MODERATION_DATABASE = 'db/moderation.json'
MODERATOR_ROLE_NAME = 'Moderator'
LOGID_MAX_TRIES = 20

class JoseMod(jaux.Auxiliar):
    def __init__(self, cl):
        '''josemod - Moderator Extension'''
        jaux.Auxiliar.__init__(self, cl)
        # TODO: Implement database
        self.moddb = {}
        self.cache = {
            'users': {},
            'ch': {}
        }

    async def ext_load(self):
        try:
            self.jsondb('moddb', path=MODERATION_DATABASE)
            return True, ''
        except Exception as err:
            return False, repr(err)

    async def ext_unload(self):
        try:
            self.jsondb_save('moddb')
            return True, ''
        except Exception as err:
            return False, repr(err)

    def channel_cache(self, channel_id):
        channel = self.client.get_channel(channel_id)

        if channel is not None:
            self.cache['ch'][channel_id] = channel

        return channel

    def get_from_data(self, server_id, field):
        data = self.moddb.get(server_id)
        if data is None:
            return

        if 'channel' in field:
            self.logger.info("[get_from_data] field %r channel %r", field, data[field])
            return self.channel_cache(data[field])
        else:
            return data.get(field)

    async def e_member_join(self, member):
        log_channel = self.get_from_data(member.server.id, 'log_channel')
        if log_channel is None:
            return

        em = discord.Embed(title='Member Join', colour=discord.Colour.green())
        em.timestamp = member.created_at
        em.set_footer(text='Created')
        em.set_author(name=str(member), icon_url=member.avatar_url or member.default_avatar_url)
        em.add_field(name='ID', value=member.id)
        em.add_field(name='Joined', value=member.joined_at)

        await self.client.send_message(log_channel, embed=em)

    async def e_member_remove(self, member):
        log_channel = self.get_from_data(member.server.id, 'log_channel')
        if log_channel is None:
            return

        em = discord.Embed(title='Member Remove', colour=discord.Colour.green())
        em.timestamp = member.created_at
        em.set_footer(text='Created')
        em.set_author(name=str(member), icon_url=member.avatar_url or member.default_avatar_url)
        em.add_field(name='ID', value=member.id)
        em.add_field(name='Removed', value=member.joined_at)

        await self.client.send_message(log_channel, embed=em)

    async def e_member_ban(self, member):
        await self.mod_log('ban', member.server, member, None)

    async def e_member_unban(self, server, user):
        await self.mod_log('unban', server, None, user, None)

    def new_log_id(self, server_id):
        data = self.moddb.get(server_id)
        if data is None:
            return

        tries = 0
        new_id = str(uuid.uuid4().fields[-1])[:5]
        while new_id in data:
            if tries >= LOGID_MAX_TRIES:
                return None

            new_id = str(uuid.uuid4().fields[-1])[:5]
            tries += 1

        return new_id

    def add_user_cache(self, userid, user):
        self.cache['users'][userid] = user

    async def get_user(self, userid):
        # get from cache if possible
        if userid in self.cache['users']:
            return self.cache['users'][userid]

        self.logger.info("[get_user] %r", userid)
        user = await self.client.get_user_info(userid)

        # cache it
        self.cache['users'][userid] = user

        return user

    async def make_log_report(self, log_title, log_id, member_id, moderator_id, reason=None):
        ban_report = []
        member = await self.get_user(member_id)
        moderator = None

        if moderator_id is not None:
            moderator = await self.get_user(moderator_id)

        ban_report.append("**%s**, log id %s" % (log_title, log_id))
        ban_report.append("**User**: %s [%s]" % (str(member), member.id))
        if reason is None:
            ban_report.append("**Reason**: **insert reason `j!reason %s`**" % log_id)
        else:
            ban_report.append("**Reason**: %s" % reason)

        if moderator_id is not None:
            ban_report.append("**Moderator**: %s [%s]" % (str(moderator), moderator.id))
        else:
            ban_report.append("**Moderator**: **No responsible moderator**")

        return ban_report

    async def mod_log(self, logtype, *data):
        server = data[0]

        self.logger.info("[mod_log:%s] %r", logtype, data)

        mod_channel = self.get_from_data(server.id, 'mod_channel')
        self.logger.info("mod_channel is %r", mod_channel)
        if mod_channel is None:
            self.logger.warning("[mod_log:%s] mod channel not found", logtype)
            return False

        log_id = self.new_log_id(server.id)
        if log_id is None:
            self.logger.warning("[mod_log:%s] error creating log ID, tried %d times", \
                logtype, LOGID_MAX_TRIES)
            return False

        log_message = None
        log_report = None
        log_data = None
        reason = None

        self.logger.info("[mod_log:%s] making mod log", logtype)

        if logtype == 'ban':
            member = data[1]
            moderator = None
            log_data = None
            if data[2] is not None:
                moderator = data[2]

            if moderator is not None:
                log_data = ['Ban', log_id, member.id, moderator.id, reason]
            else:
                log_data = ['Ban', log_id, member.id, None, reason]

            log_report = await self.make_log_report(*log_data)

        elif logtype == 'unban':
            moderator = data[1]
            user = data[2]
            reason = data[3]

            if moderator is None:
                log_data = ['Unban', log_id, user.id, None, reason]
            else:
                log_data = ['Unban', log_id, user.id, moderator.id, reason]

            log_report = await self.make_log_report(*log_data)

        elif logtype == 'softban':
            member = data[1]
            moderator = data[2]

            log_data = ['Softban', log_id, member.id, moderator.id, reason]
            log_report = await self.make_log_report(*log_data)

        elif logtype == 'kick':
            member = data[1]
            moderator = data[2]
            log_data = ['Kick', log_id, member.id, moderator.id, reason]
            log_report = await self.make_log_report(*log_data)

        elif logtype == 'reason':
            log_id = data[1]
            reason = data[2]

            if reason is None:
                return False

            data = self.moddb.get(server.id)
            if data is None:
                return False

            log = data['logs'].get(log_id, None)
            if log is None:
                return False

            # overwrite reason
            log['data'][4] = reason

            logmsg = await self.client.get_message(mod_channel, log['msg_id'])
            new_report = await self.make_log_report(*log['data'])
            log_message = await self.client.edit_message(logmsg, \
                '\n'.join(new_report))

            # copy
            log_data = copy.copy(log['data'])

        if logtype != 'reason':
            log_message = await self.client.send_message(mod_channel, \
                '\n'.join(log_report))

        self.moddb[server.id]['logs'][log_id] = {
            'type': logtype,
            'data': log_data,
            'timestamp': time.time(),
            'msg_id': log_message.id,
        }

        return True

    async def can_do(self, action, user):
        # TODO: specific actions to certain roles
        if user.id in jcommon.ADMIN_IDS:
            return True

        for role in user.roles:
            if role.name == MODERATOR_ROLE_NAME:
                return True

        raise je.PermissionError()

    async def has_mod_system(self, server):
        if server.id in self.moddb:
            return True
        else:
            raise je.CommonError("Moderation System is not enabled in this server.")

    async def c_initmod(self, message, args, cxt):
        '''`j!initmod modchannel logchannel` - Initialize Moderator extension in this server'''
        await self.is_admin(message.author.id)

        if len(args) < 3:
            await cxt.say(self.c_initmod.__doc__)
            return

        server = message.server
        server_id = message.server.id

        if server_id in self.moddb:
            await cxt.say("Moderator is already running on in this server")
            return

        try:
            mod_channel_name = args[1]
            log_channel_name = args[2]
        except:
            await cxt.say("???")
            return

        # everyone can read, only jose can write
        everyone_perms = discord.PermissionOverwrite(read_messages=True, write_messages=False)
        my_perms = discord.PermissionOverwrite(read_messages=True, write_messages=True)

        everyone = discord.ChannelPermissions(target=server.default_role, overwrite=everyone_perms)
        jose = discord.ChannelPermissions(target=server.me, overwrite=my_perms)

        try:
            mod_channel = await self.client.create_channel(server, \
                mod_channel_name, everyone, jose)
            log_channel = await self.client.create_channel(server, \
                log_channel_name, everyone, jose)
        except discord.Forbidden:
            await cxt.say("hey I can't create channels give me permissions")
            return

        self.moddb[server_id] = {
            'mod_channel': mod_channel.id,
            'log_channel': log_channel.id,
            'logs': {
                '0': 'Genesis log'
            },
        }

        return

    async def c_kick(self, message, args, cxt):
        '''`j!kick @mention` - kicks a user'''
        await self.can_do('kick', message.author)
        await self.has_mod_system(message.server)

        if len(args) < 2:
            await cxt.say(self.c_kick.__doc__)
            return

        try:
            userid = await jcommon.parse_id(args[1])
        except:
            await cxt.say("Error parsing `@mention`")
            return

        member = message.server.get_member(userid)
        self.add_user_cache(userid, member)
        self.add_user_cache(message.author.id, message.author)

        try:
            await self.client.kick(member)
            done = await self.mod_log('kick', message.server, member, message.author)
            if done:
                await cxt.say(':boxing_glove: **%s kicked**', (str(member),))
            else:
                await cxt.say(':thinking:')

        except discord.Forbidden:
            await cxt.say('Not enough permissions to kick.')
            return
        except discord.HTTPException:
            await cxt.say('Error kicking.')
            return
        except Exception as err:
            await cxt.say(':thinking: `%r`', (err,))
            return

    async def c_ban(self, message, args, cxt):
        '''`j!ban @mention [reason]` - bans a user'''
        await self.can_do('ban', message.author)
        await self.has_mod_system(message.server)

        if len(args) < 2:
            await cxt.say(self.c_kick.__doc__)
            return

        try:
            userid = await jcommon.parse_id(args[1])
        except:
            await cxt.say("Error parsing `@mention`")
            return

        member = message.server.get_member(userid)

        self.add_user_cache(userid, member)
        self.add_user_cache(message.author.id, message.author)

        try:
            await self.client.ban(member)
        except discord.Forbidden:
            await cxt.say('Not enough permissions to ban.')
            return
        except discord.HTTPException:
            await cxt.say('Error banning.')
            return
        else:
            await cxt.say(':hammer: **%s was banned**', (str(member),))

        await self.mod_log('ban', message.server, member, message.author)

    async def c_unban(self, message, args, cxt):
        '''`j!unban caseid reason` - unbans a user'''

        try:
            log_id = args[1]
        except:
            await cxt.say("Error parsing `caseid`")
            return

        try:
            reason = ' '.join(args[2:])
        except:
            await cxt.say("Error parsing `reason`")

        self.add_user_cache(message.author.id, message.author)
        server = message.server

        mod_data = self.moddb.get(server.id)
        if mod_data is None:
            return False

        log = mod_data['logs'].get(log_id, None)
        if log is None:
            return False

        log_data = log['data']
        if log_data is None:
            await cxt.say("?????? `%r`", (log,))
            return

        # log_data[2] has user ID
        user = await self.client.get_user_info(log_data[2])
        self.add_user_cache(log_data[2], user)

        try:
            await self.client.unban(server, user)
        except discord.Forbidden:
            await cxt.say('Not enough permissions to unban.')
            return
        except discord.HTTPException:
            await cxt.say('Error unbanning.')
            return
        else:
            await cxt.say(':angel: **%s was unbanned**', (str(user),))

        await self.mod_log('unban', message.server, user, message.author, reason)

    async def c_reason(self, message, args, cxt):
        '''`j!reason caseid reason` - Sets a reason for a kick/ban/etc'''
        await self.can_do('reason', message.author)
        await self.has_mod_system(message.server)

        if len(args) < 2:
            await cxt.say(self.c_reason.__doc__)
            return

        try:
            log_id = args[1]
        except:
            await cxt.say("Error parsing `caseid`")
            return

        try:
            reason = ' '.join(args[2:])
        except:
            await cxt.say("Error parsing `reason`")

        done = await self.mod_log('reason', message.server, log_id, reason)
        if done:
            await cxt.say(":ok_hand: Reason processed")
        else:
            await cxt.say(":thinking:")

        return
