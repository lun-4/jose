#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import jauxiliar as jaux
import joseerror as je

class JoseMod(jaux.Auxiliar):
    def __init__(self, cl):
        '''josemod - Moderator Extension'''
        jaux.Auxiliar.__init__(self, cl)
        # TODO: Implement database
        self.moddb = {}
        self.cache = {}

        # TODO: commands for josemod

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

    async def e_member_join(self, member):
        data = self.moddb(member.server.id)
        if data is None:
            return

        log_channel = await self.get_channel(data['log_channel'])
        if log_channel is None:
            return

        em = discord.Embed(title='Member Join', colour=discord.Colour.green())
        em.timestamp = member.created_at
        em.set_footer(text='Created')
        em.set_author(name=str(member), icon_url=member.avatar_url or member.default_avatar_url)
        em.add_field(name='ID', value=member.id)
        em.add_field(name='Joined', value=member.joined_at)

        await cxt.say_embed(em, log_channel)

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
            'bans': {},
            'kicks': {},
        }

        return

    async def c_kick(self, message, args, cxt):
        '''`j!kick @mention` - kicks a user'''
        await self.is_admin(message.author.id)

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
        except discord.HTTPException:
            await cxt.say('Error kicking.')
        else:
            await cxt.say(':boxing_glove: kicked')

    async def c_reason(self, message, args, cxt):
        '''`j!reason id reason` - Sets a reason for a kick/ban/etc'''
        await self.is_admin(message.author.id)

        if len(args) < 2:
            await cxt.say(self.c_reason.__doc__)

        return
