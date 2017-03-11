#!/usr/bin/env python3

import discord
import sys
sys.path.append("..")
import jauxiliar as jaux
import joseerror as je
import josecommon as jcommon
import uuid
import time

MODERATOR_ROLE_NAME = 'Moderator'

class JoseMod(jaux.Auxiliar):
    def __init__(self, cl):
        '''josemod - Moderator Extension'''
        jaux.Auxiliar.__init__(self, cl)
        # TODO: Implement database
        self.moddb = {}
        self.cache = {
            'users': {}
        }

    async def ext_load(self):
        return True, ''

    async def ext_unload(self):
        return True, ''

    async def get_channel(self, server_id, channel_id):
        servers = [server for server in self.client.servers if server.id == server_id]

        if len(servers) == 0 or len(servers) > 1:
            return None

        server = servers[0]
        channel = server.get_channel(channel_id)

        if channel is not None:
            if server_id not in self.cache:
                self.cache[server_id] = {}

            self.cache[server_id][channel_id] = channel

        return channel

    async def get_from_data(self, server_id, field):
        data = self.moddb.get(server_id)
        if data is None:
            return

        if 'channel' in field:
            value = await self.get_channel(data[field])
            if value is None:
                return
            return value
        else:
            return data.get(field)

    async def e_member_join(self, member):
        log_channel = await self.get_from_data(member.server.id, 'log_channel')
        if log_channel is None:
            return

        em = discord.Embed(title='Member Join', colour=discord.Colour.green())
        em.timestamp = member.created_at
        em.set_footer(text='Created')
        em.set_author(name=str(member), icon_url=member.avatar_url or member.default_avatar_url)
        em.add_field(name='ID', value=member.id)
        em.add_field(name='Joined', value=member.joined_at)

        await self.client.send_message(embed=em, channel=log_channel)

    def new_log_id(self, server_id):
        data = self.moddb.get(server_id)
        if data is None:
            return

        new_id = '0'
        took = 1
        while new_id in data:
            new_id = str(uuid.uuid4().fields[-1])[:5]
            took += 1

        return new_id

    async def get_user(self, userid):
        # get from cache if possible
        if userid in self.cache['users']:
            return self.cache['users'][userid]

        user = await self.client.get_user_info(userid)
        # cache it
        self.cache['users'][userid] = user

    async def make_log_report(self, log_title, log_id, member_id, moderator_id, reason=None):
        ban_report = []
        member = await self.get_user(member_id)
        moderator = await self.get_user(moderator_id)

        ban_report.append("**%s**, log number %d" % (log_title, log_id))
        ban_report.append("**User**: %s [%s]" % (str(member), member.id))
        if reason is None:
            ban_report.append("**Reason**: **insert reason `j!reason %d`**" % log_id)
        else:
            ban_report.append("**Reason**: %s" % reason)
        ban_report.append("**Moderator**: %s [%s]" % (str(moderator), moderator.id))
        return ban_report

    async def mod_log(self, logtype, *data):
        server = data[0]

        mod_channel = await self.get_from_data(server.id, 'mod_channel')
        if mod_channel is None:
            return

        log_id = self.new_log_id(server.id)
        log_report = None
        log_data = None
        reason = None

        if logtype == 'ban':
            member = data[1]
            moderator = data[2]
            log_data = ['Ban', log_id, member.id, moderator.id, reason]
            log_report = await self.make_log_report(**log_data)

        elif logtype == 'unban':
            moderator = data[1]
            user_id = data[2]
            log_data = ['Unban', log_id, user_id, moderator.id, reason]
            log_report = await self.make_log_report(**log_data)

        elif logtype == 'softban':
            member = data[1]
            moderator = data[2]

            log_data = ['Softban', log_id, member.id, moderator.id, reason]
            log_report = await self.make_log_report(**log_data)

        elif logtype == 'kick':
            member = data[1]
            moderator = data[2]
            log_data = ['Kick', log_id, member.id, moderator.id, reason]
            log_report = await self.make_log_report(**log_data)

        elif logtype == 'reason':
            log_id = data[0]
            log = self.moddb[server.id]['logs'][log_id]

            # overwrite reason
            log['data'][4] = data[1]

            logmsg = await self.client.get_message(mod_channel, log['msg_id'])
            new_report = await self.make_log_report(**log['data'])
            await self.client.edit_message(logmsg, new_report)

        if logtype != 'reason':
            log_message = await self.client.send_message('\n'.join(log_report), \
                channel=mod_channel)

        self.moddb[server.id]['logs'][log_id] = {
            'type': logtype,
            'data': log_data,
            'timestamp': time.time(),
            'msg_id': log_message.id,
        }

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

        try:
            userid = await jcommon.parse_id(args[1])
        except:
            await cxt.say("Error parsing `@mention`")
            return

        member = message.server.get_member(userid)

        try:
            await self.client.kick(member)
        except discord.Forbidden:
            await cxt.say('Not enough permissions to kick.')
            return
        except discord.HTTPException:
            await cxt.say('Error kicking.')
            return
        else:
            await cxt.say(':boxing_glove: **%s kicked**', (str(member),))

        await self.mod_log('kick', member, message.author)

    async def c_ban(self, message, args, cxt):
        '''`j!ban @mention [reason]` - bans a user'''
        await self.can_do('ban', message.author)
        await self.has_mod_system(message.server)

        if len(args) < 2:
            await cxt.say(self.c_kick.__doc__)

        try:
            userid = await jcommon.parse_id(args[1])
        except:
            await cxt.say("Error parsing `@mention`")
            return

        member = message.server.get_member(userid)

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

        await self.mod_log('ban', member, message.author)

    async def c_reason(self, message, args, cxt):
        '''`j!reason id reason` - Sets a reason for a kick/ban/etc'''
        await self.can_do('reason', message.author)
        await self.has_mod_system(message.server)

        if len(args) < 2:
            await cxt.say(self.c_reason.__doc__)

        try:
            log_id = args[1]
        except:
            await cxt.say("Error parsing `id`")
            return

        try:
            reason = ' '.join(args[2:])
        except:
            await cxt.say("Error parsing `reason`")

        await self.mod_log(self, 'reason', log_id, reason)

        return
