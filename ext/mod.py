import datetime

import discord
from discord.ext import commands

from .common import Cog


class Actions:
    """Moderation actions."""
    REASON = 0
    KICK = 1
    BAN = 2
    UNBAN = 3
    SOFTBAN = 4

ACTION_AS_AUDITLOG = [None, 'kick', 'ban', 'unban', None]


def is_moderator():
    def _is_moderator(ctx):
        member = ctx.guild.get_member(ctx.author.id)
        perms = ctx.channel.permissions_for(member)
        return (ctx.author.id == ctx.bot.owner_id) or perms.kick_members or perms.ban_members 
    
    return commands.check(_is_moderator)


class Moderation(Cog):
    """Moderation system."""
    def __init__(self, bot):
        super().__init__(bot)
        self.modcfg_coll = self.config.jose_db['mod_config']
        self.cache = {}

        self.handlers = {
            Actions.REASON: self.reason_handler,
            Actions.KICK: self.kick_handler,
            Actions.BAN: self.ban_handler,
            Actions.UNBAN: self.unban_handler,
        }

    def account_age(self, t):
        now = datetime.datetime.now()
        return str(now - t)

    async def modcfg_get(self, guild, field=None):
        """Get a field from a mod config object."""
        modconfig = await self.modcfg_coll.find_one({'guild_id': guild.id})
        if modconfig is None:
            return None

        if field is None:
            return modconfig
        return modconfig.get(field)

    async def _modcfg_get(self, guild):
        modconfig = await self.modcfg_get(guild)
        if modconfig is None:
            raise self.SayException('Mod ocnfiguration not found')

        return modconfig

    async def on_member_join(self, member):
        """Called upon any member join"""
        logchan_id = await self.modcfg_get(member.guild, 'member_log_id')
        logchannel = self.bot.get_channel(logchan_id)
        if logchan_id is None or logchannel is None: return

        em = discord.Embed(title='Member Join', colour=discord.Colour.green())
        em.timestamp = member.joined_at

        em.set_footer(text='Created')

        em.set_author(name=str(member), icon_url=member.avatar_url or member.default_avatar_url)
        
        em.add_field(name='ID', value=member.id)
        em.add_field(name='Account age', value=f'`{self.account_age(member.created_at)}`')

        await logchannel.send(embed=em)

    async def on_member_remove(self, member):
        """Called upon member remove."""
        logchan_id = await self.modcfg_get(member.guild, 'member_log_id')
        logchannel = self.bot.get_channel(logchan_id)
        if logchan_id is None or logchannel is None: return

        em = discord.Embed(title='Member Remove', colour=discord.Colour.red())
        em.timestamp = datetime.datetime.now() 

        em.set_footer(text='Created')
        em.set_author(name=str(member), icon_url=member.avatar_url or member.default_avatar_url)
        
        em.add_field(name='ID', value=member.id)
        em.add_field(name='Account age', value=f'`{self.account_age(member.created_at)}`')
        em.add_field(name='Server age', value=f'`{self.account_age(member.joined_at)}`')

        await logchannel.send(embed=em)

    async def on_member_ban(self, guild, user):
        modconfig = await self.modcfg_get(guild)
        if modconfig is None:
            return

        await self.modlog(Actions.BAN, guild, user, modconfig=modconfig)

    async def on_member_unban(self, guild, user):
        modconfig = await self.modcfg_get(guild)
        if modconfig is None:
            return

        await self.modlog(Actions.UNBAN, guild, user, modconfig=modconfig)

    def modlog_fmt(self, data):
        user = data['user']
        fmt = (f'**{ACTION_AS_AUDITLOG[data["action"]].capitalize()}** | Case {data["action_id"]}\n'
                f'**User**: {str(user)} ({user.id})\n'
                f'**Reason**: {data["reason"].get("reason") or "No reason provided"}\n'
                f'**Responsible Moderator**: {str(data.get("reason", {}).get("moderator", None))}\n') 
        return fmt

    async def add_mod_entry(self, modcfg, data):
        """Add a moderation entry to the moderation channel"""
        mod_log_id = modcfg['mod_log_id']
        modlog = data['guild'].get_channel(mod_log_id)
        if modlog is None:
            raise self.SayException('Moderation channel not found')

        m = await modlog.send(self.modlog_fmt(data))
        self.cache[data['action_id']] = {'message_id': m.id, 'data': data}

    async def edit_mod_entry(self, modcfg, data):
        """Edit a moderation entry."""
        modlog = data['guild'].get_channel(modcfg['mod_log_id'])
        if modlog is None:
            raise self.SayException('Moderation channel not found')

        try:
            action_data = self.cache[data['action_id']]
        except KeyError:
            raise self.SayException("Can't find action ID in cache, sorry :c")

        old_data = action_data['data']
        old_data['reason'] = data['reason']

        try:
            message = await modlog.get_message(action_data['message_id'])
        except discord.NotFound:
            raise self.SayException('Message to edit not found')
        except discord.Forbidden:
            raise self.SayException("Can't read messages")
        except discord.HTTPException as err:
            raise self.SayException(f'fug `{err!r}`')

        await message.edit(content=self.modlog_fmt(old_data))

    async def kick_handler(self, modcfg, guild, user, reason, **kwargs): 
        """Handle the 'kick' action, creates an entry."""
        data = {
            'guild': guild,
            'user': user,
            'reason': reason,
            'action': Actions.KICK,
            'action_id': modcfg['last_action_id'] + 1,
        }

        await self.modcfg_coll.update_one({'guild_id': guild.id}, {'$inc': {'last_action_id': 1}})
        await self.add_mod_entry(modcfg, data)
    
    async def ban_handler(self, modcfg, guild, user, reason, **kwargs): 
        """Handle the 'ban' action, creates an entry."""
        data = {
            'guild': guild,
            'user': user,
            'reason': reason,
            'action': Actions.BAN,
            'action_id': modcfg['last_action_id'] + 1,
        }

        await self.modcfg_coll.update_one({'guild_id': guild.id}, {'$inc': {'last_action_id': 1}})
        await self.add_mod_entry(modcfg, data)

    async def reason_handler(self, modcfg, guild, user, reason, **kwargs):
        """Add a reason to an action, doesn't edit audit logs(since it isn't possible)."""
        data = {
            'guild': guild,
            'user': user,
            'reason': reason,
            'action': Actions.REASON,
            'action_id': kwargs['action_id'],
        }

        await self.edit_mod_entry(modcfg, data)

    async def unban_handler(self, modcfg, guild, user, reason, **kwargs):
        """Add an entry for user unbanning."""
        data = {
            'guild': guild,
            'user': user,
            'reason': reason,
            'action': Actions.UNBAN,
            'action_id': modcfg['last_action_id'] + 1,
        }
        await self.add_mod_entry(modcfg, data)

    async def modlog(self, action, guild, user, **kwargs):
        """Add a moderation entry.

        This creates/edits a message in the moderation log channel with respective
        data about the action user and moderator that did the action.

        If a reason is not provided, this polls the guild's audit logs.
        
        Parameters
        ----------
        action: int
            Action to be logged, :meth:`Actions` describes them..
        guild: discord.Guild
            The guild this moderation entry is going to.
        user: discord.User
            The user the moderation entry is reffering.
        **kwargs: dict
            keyword-arguments you can use to save the method to query mongo
            or insert a reason to the moderation entry.
        """
        reason = kwargs.get('reason')
        if reason is None:
            # poll audit logs
            reason = {}
            action_as_auditlog = getattr(discord.AuditLogAction, ACTION_AS_AUDITLOG[action])
            try:
                async for entry in guild.audit_logs(limit=10):
                    if entry.target.id != user.id:
                        continue

                    if entry.action != action_as_auditlog:
                        continue

                    try:
                        reason['moderator'] = user
                        reason['reason'] = entry.reason
                    except AttributeError:
                        reason['reason'] = None
            except discord.Forbidden:
                raise self.SayException("Can't access audit logs.")
            except discord.HTTPException as err:
                await self.SayException(f'fug `{err!r}`')

        modconfig = kwargs.get('modconfig')
        if modconfig is None:
            # get modconfig
            modconfig = await self._modcfg_get(guild)
        
        handler = self.handlers[action]
        try:
            kwargs.pop('reason') # because we already give the reason to handler
        except KeyError:
            pass

        await handler(modconfig, guild, user, reason, **kwargs)

    @commands.command()
    @commands.is_owner()
    async def modattach(self, ctx, memberlog: discord.TextChannel, modlog: discord.TextChannel):
        """Attach channels to the moderation system"""
        modconfig = await self.modcfg_get(ctx.guild)
        if modconfig is not None:
            raise self.SayException('Mod config already exists.')

        modconfig = {
            'guild_id': ctx.guild.id,
            'member_log_id': memberlog.id,
            'mod_log_id': modlog.id,
            'last_action_id': 0,
        }

        res = await self.modcfg_coll.insert_one(modconfig)
        await ctx.success(res.acknowledged)

    @commands.command()
    @is_moderator()
    async def reason(self, ctx, action_id: int, *, reason: str):
        """Add a reason to a moderator action.
        
        As soon as you use that command, you become
        the responsible moderator of the action.
        """
        modconfig = await self._modcfg_get(ctx.guild)
        _reason = {'reason': reason, 'moderator': ctx.author}
        await self.modlog(Actions.REASON, ctx.guild, None, reason=_reason, action_id=action_id, modconfig=modconfig)
        await ctx.ok()

    @commands.command()
    @is_moderator()
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        """Kick someone and add it in the mod logs and audit logs."""
        modconfig = await self._modcfg_get(ctx.guild)

        try:
            await member.kick(reason=reason)
        except discord.Forbidden:
            raise self.SayException("can't kick >:c")
        except discord.HTTPException as err:
            raise self.SayException('wtf is happening discord `{err!r}`')

        _reason = {'reason': reason, 'moderator': ctx.author}
        await self.modlog(Actions.KICK, ctx.guild, member, reason=_reason, modconfig=modconfig)
        await ctx.ok()

    @commands.command()
    @is_moderator()
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
        """Bans someone and add it to mod logs."""
        modconfig = await self._modcfg_get(ctx.guild)

        try:
            await member.ban(reason=reason)
        except discord.Forbidden:
            raise self.SayException("can't ban u suck ass >:c")
        except discord.HTTPException as err:
            raise self.SayException('wtf is happening discord `{err!r}`')

        _reason = {'reason': reason, 'moderator': ctx.author}
        await self.modlog(Actions.BAN, ctx.guild, member, reason=_reason, modconfig=modconfig)
        await ctx.ok()


def setup(bot):
    bot.add_cog(Moderation(bot))
