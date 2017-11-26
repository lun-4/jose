import collections
import asyncio
import random
import logging
import re

import discord

from discord.ext import commands

from .common import Cog

log = logging.getLogger(__name__)

IMAGE_REGEX = re.compile('(https?:\/\/.*\.(?:png|jpeg|jpg|gif))', re.M | re.I)


BLUE = 0x0066ff
BRONZE = 0xc67931
SILVER = 0xC0C0C0
GOLD = 0xD4AF37
RED = 0xff0000
WHITE = 0xffffff


class StarAddError(Exception):
    pass


class StarRemoveError(Exception):
    pass


class StarError(Exception):
    pass


def empty_star_object(message):
    return {
        'message_id': message.id,
        'channel_id': message.channel.id,
        'guild_id': message.guild.id,
        'starrers': [],
    }


def empty_starconfig(guild):
    log.info(f'Generating starconfig for [{guild!s} {guild.id}]')
    return {
        'guild_id': guild.id,
        'starboard_id': None,
    }


def get_humans(message):
    l = sum(1 for m in message.guild.members if not m.bot)

    # Since selfstarring isn't allowed,
    # we need to remove 1 from the total amount.
    l -= 1

    if l < 0:
        return 1

    return l


def make_color(star, message):
    color = 0x0
    stars = len(star['starrers'])

    star_ratio = stars / get_humans(message)

    if star_ratio >= 0:
        color = RED
    if star_ratio >= 0.1:
        color = BLUE
    if star_ratio >= 0.2:
        color = BRONZE
    if star_ratio >= 0.4:
        color = SILVER
    if star_ratio >= 0.8:
        color = GOLD
    if star_ratio >= 1:
        color = WHITE

    return color


def get_emoji(star, message):
    emoji = ''
    stars = len(star['starrers'])

    star_ratio = stars / get_humans(message)

    if star_ratio >= 0:
        emoji = '<:josestar1:353997747772456980>'
    if star_ratio >= 0.1:
        emoji = '<:josestar2:353997748216922112>'
    if star_ratio >= 0.2:
        emoji = '<:josestar3:353997748288225290>'
    if star_ratio >= 0.4:
        emoji = '<:josestar4:353997749341126657>'
    if star_ratio >= 0.8:
        emoji = '<:josestar5:353997749949300736>'
    if star_ratio >= 1:
        emoji = '<:josestar6:353997749630402561>'

    return emoji


def make_star_embed(star, message):
    """Create the starboard embed."""
    star_emoji = get_emoji(star, message)
    embed_color = make_color(star, message)

    title = f'{len(star["starrers"])} {star_emoji} {message.channel.mention}, ID: {message.id}'

    content = message.content
    em = discord.Embed(description=content, colour=embed_color)
    em.timestamp = message.created_at

    au = message.author
    avatar = au.avatar_url or au.default_avatar_url
    em.set_author(name=au.display_name, icon_url=avatar)

    # check for image urls
    search_res = IMAGE_REGEX.search(content)
    if search_res:
        em.set_image(url=search_res.group(0))

    attch = message.attachments
    if attch:
        attch_url = attch[0].url
        if attch_url.lower().endswith(('png', 'jpeg', 'jpg', 'gif',)):
            em.set_image(url=attch_url)
        else:
            attachments = '\n'.join([f'[Attachment]({attch_s["url"]})'
                                     for attch_s in attch])
            em.description += attachments

    return title, em


def check_nsfw(guild, config, message):
    starboard = guild.get_channel(config['starboard_id'])
    if starboard is None:
        raise StarError('No starboard found')

    nsfw_starboard = starboard.is_nsfw()
    nsfw_message = message.channel.is_nsfw()
    if nsfw_starboard:
        return

    if nsfw_message:
        raise StarError('NSFW message in SFW starboard')


class Starboard(Cog):
    """Starboard.

    lol starboard u kno the good shit
    """
    def __init__(self, bot):
        super().__init__(bot)
        self.bot.simple_exc.extend([StarError, StarAddError, StarRemoveError])

        # prevent race conditions
        self._locks = collections.defaultdict(asyncio.Lock)

        # janitor
        #: the janitor semaphore keeps things up and running
        #  by only allowing 1 janitor task each time.
        #  a janitor task cleans stuff out of mongo
        self.janitor_semaphore = asyncio.Semaphore(1)

        # collectiones
        self.starboard_coll = self.config.jose_db['starboard']
        self.starconfig_coll = self.config.jose_db['starconfig']

    async def get_starconfig(self, guild_id: int) -> dict:
        """Get a starboard configuration object for a guild.

        If the guild is blocked, deletes the starboard configuration.
        """

        if await self.bot.is_blocked_guild(guild_id):
            g = self.bot.get_guild(guild_id)

            r = await self.starconfig_coll.delete_many({'guild_id': guild_id})
            log.info(f'Deleted {r.deleted_count} sconfig: `{g.name}[g.id]` from blocking')
            return

        return await self.starconfig_coll.find_one({'guild_id': guild_id})

    async def _get_starconfig(self, guild_id: int) -> dict:
        """Same as :meth:`Starboard.get_starconfig` but raises `StarError` when
        no configuration is found.
        """
        cfg = await self.get_starconfig(guild_id)
        if not cfg:
            raise StarError('No starboard configuration was found for this guild')

        return cfg

    async def get_star(self, guild_id: int, message_id: int):
        """Get a star object from a guild+message ID pair."""
        return await self.starboard_coll.find_one({'message_id': message_id,
                                                   'guild_id': guild_id})

    async def janitor_task(self, guild_id: int):
        """Deletes all star objects that refer to a specific Guild ID.

        This will aquire the :attr:`Stars.janitor_semaphore` semaphore,
        and because of that, it will block the calling coroutine until some other
        coroutine releases the semaphore.
        """
        try:
            await self.janitor_semaphore.acquire()

            log.warning('[janitor] deleting star objectss from %d', guild_id)
            res = await self.starboard_coll.delete_many({'guild_id': guild_id})
            g = self.bot.get_guild(guild_id)

            log.warning('[janitor] Deleted %d star objects from janitoring %s[%d]',
                        res.deleted_count, g.name, g.id)

        except:
            log.exception('error on janitor task')
        finally:
            self.janitor_semaphore.release()

    async def raw_add_star(self, config: dict, message: discord.Message,
                           author_id: int) -> dict:
        """Add a star to a message.

        Returns
        -------
        dict
            Created star object.
        """
        guild_id = config['guild_id']
        guild = message.guild

        check_nsfw(guild, config, message)

        # check if we already have a star or not
        star = await self.get_star(guild_id, message.id)

        if not star:
            star_object = empty_star_object(message)
            res = await self.starboard_coll.insert_one(star_object)

            if not res.acknowledged:
                raise StarAddError('Insert OP not acknowledged by db')

            star = star_object

        try:
            star['starrers'].index(author_id)
            raise StarAddError('Already starred')
        except ValueError:
            star['starrers'].append(author_id)

        await self.update_starobj(star)
        return star

    async def raw_remove_star(self, config: dict, message: discord.Message,
                              author_id: int) -> dict:
        """Remove a star from someone, updates the star object
        in the starboard collection.

        Returns
        -------
        dict
            Modified star object
        """
        guild_id = config['guild_id']
        star = await self.get_star(guild_id, message.id)
        if star is None:
            raise StarRemoveError('No message starred to be unstarred')

        try:
            star['starrers'].index(author_id)
            star['starrers'].remove(author_id)
        except ValueError:
            raise StarRemoveError("Author didn't star the message.")

        if len(star['starrers']) < 1:
            res = await self.starboard_coll.delete_many(
                {'message_id': message.id, 'guild_id': guild_id})

            if res.deleted_count != 1:
                log.error(f'Deleted {res.deleted_count} document from 0 stars,'
                          ' different than 1')
            return star

        await self.starboard_coll.update_one({'message_id': message.id,
                                              'guild_id': guild_id},
                                             {'$set': star})
        return star

    async def raw_remove_all(self, config: dict,
                             message: discord.Message) -> dict:
        """Remove all starrers from a message(deletes from the collection)."""
        guild_id = config['guild_id']
        star = await self.get_star(guild_id, message.id)
        if star is None:
            raise StarError('Star object not found to be reset')

        star['starrers'] = []
        await self.starboard_coll.delete_one({'message_id': message.id,
                                              'guild_id': guild_id})
        return star

    async def update_starobj(self, star):
        log.debug('Updating star `mid=%d cid=%d gid=%d`',
                  star.get('message_id'), star.get('channel_id'),
                  star.get('guild_id'))

        await self.starboard_coll.update_one({'guild_id': star['guild_id'],
                                              'message_id': star['message_id']},
                                             {'$set': star})

    async def delete_starobj(self, star, msg=None):
        """Delete a star object from the starboard collection.
        Removes the message from starboard if provided.
        """
        if msg is not None:
            await msg.delete()

        log.debug('Deleting star `mid=%d cid=%d gid=%d`',
                  star.get('message_id'), star.get('channel_id'),
                  star.get('guild_id'))

        return await self.starboard_coll.delete_one(
            {'guild_id': star['guild_id'], 'message_id': star['message_id']})

    async def starboard_send(self, starboard: discord.TextChannel, star: dict,
                             message: discord.Message) -> discord.Message:
        """Sends a message to the starboard."""
        title, embed = make_star_embed(star, message)
        return await starboard.send(title, embed=embed)

    async def update_star(self, config, star, **kwargs):
        """Update a star.

        Posts it to the starboard, edits if a message already exists.

        Parameters
        ----------
        config: dict
            Starboard configuration for the guild.
        star: dict
            Star object being updated.
        delete: bool, optional
            If this should delete the star.
        msg: discord.Message, optional
            A message object reffering to the star.

        Raises
        ------
        StarError
            For any error that happened while updating that star.
        """

        delete_mode = kwargs.get('delete', False)
        message = kwargs.get('msg')

        if message is not None:
            assert star['message_id'] == message.id
            assert star['channel_id'] == message.channel.id

        guild_id = config['guild_id']
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            raise StarError('No guild found with the starboard configuration')

        starboard = guild.get_channel(config['starboard_id'])
        if starboard is None:
            await self.delete_starconfig(config)
            raise StarError('No starboard channel found')

        try:
            star_message = await starboard.get_message(star['star_message_id'])
        except KeyError:
            star_message = None

        if delete_mode or len(star['starrers']) < 1:
            await self.delete_starobj(star, msg=star_message)
            return

        # do update/send here
        if star_message is None:
            star_message = await self.starboard_send(starboard, star, message)
            star['star_message_id'] = star_message.id
            await self.update_starobj(star)
        else:
            title, embed = make_star_embed(star, kwargs.get('msg'))
            await star_message.edit(content=title, embed=embed)

        return

    async def add_star(self, message: discord.Message,
                       author_id: int, config: dict = None) -> dict:
        """Add a star to a message.

        Parameters
        ----------
        message: `discord.Message`
            Message to be starred.
        author_id: int
            Author ID of the star.

        Raises
        ------
        StarAddError
            If any kind of error happened while adding the star.
        """
        lock = self._locks[message.guild.id]
        await lock
        star = None

        try:
            if not config:
                config = await self._get_starconfig(message.guild.id)

            if hasattr(author_id, 'id'):
                author_id = author_id.id

            if author_id == message.author.id:
                raise StarAddError('No selfstarring allowed')

            star = await self.raw_add_star(config, message, author_id)
            star = await self.update_star(config, star, msg=message)
        finally:
            lock.release()

        return star

    async def remove_star(self, message: discord.Message,
                          author_id: int, config: dict=None) -> dict:
        """Remove a star from a message.

        Parameters
        ----------
        message: `discord.Message`
            Message.
        author_id: int
            ID of the person that is getting their star removed.

        Raises
        ------
        StarRemoveError
            Any kind of error while remoing the star.
        """
        lock = self._locks[message.guild.id]
        await lock
        star = None

        try:
            if not config:
                config = await self._get_starconfig(message.guild.id)

            if hasattr(author_id, 'id'):
                author_id = author_id.id

            if author_id == message.author.id:
                raise StarRemoveError('No selfstarring allowed')

            star = await self.raw_remove_star(config, message, author_id)
            star = await self.update_star(config, star, msg=message)
        finally:
            lock.release()

        return star

    async def remove_all(self, message: discord.Message, config: dict=None):
        """Remove all stars from a message.

        Parameters
        ----------
        message: `discord.Message`
            Message that is going to have all stars removed.
        """
        lock = self._locks[message.guild.id]
        await lock

        try:
            if not config:
                config = await self._get_starconfig(message.guild.id)

            star = await self.raw_remove_all(config, message)
            await self.update_star(config, star, delete=True)
        finally:
            lock.release()

    async def delete_starconfig(self, config: dict) -> bool:
        """Deletes a starboard configuration from the collection.

        Returns
        -------
        bool
            Success/Failure of the operation.
        """
        guild = self.bot.get_guild(config['guild_id'])
        log.debug('Deleting starconfig for %s[%d]',
                  guild.name, guild.id)

        res = await self.starconfig_coll.delete_many(config)
        return res.deleted_count > 0

    async def on_raw_reaction_add(self, emoji_partial,
                                  message_id, channel_id, user_id):
        if emoji_partial.is_custom_emoji():
            return

        if emoji_partial.name != '⭐':
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        cfg = await self.get_starconfig(channel.guild.id)
        if not cfg:
            return

        message = await channel.get_message(message_id)

        try:
            await self.add_star(message, user_id, cfg)
        except (StarError, StarAddError) as err:
            log.warning(f'raw_reaction_add: {err!r}')
        except Exception:
            log.excpetion('add_star @ reaction_add, %s[cid=%d] %s[gid=%d]',
                          channel.name, channel.id,
                          channel.guild.name, channel.guild.id)

    async def on_raw_reaction_remove(self, emoji_partial,
                                     message_id, channel_id, user_id):
        if emoji_partial.is_custom_emoji():
            return

        if emoji_partial.name != '⭐':
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        cfg = await self.get_starconfig(channel.guild.id)
        if not cfg:
            return

        message = await channel.get_message(message_id)
        try:
            await self.remove_star(message, user_id, cfg)
        except (StarError, StarRemoveError) as err:
            log.warning(f'raw_reaction_remove: {err!r}')
        except Exception:
            log.excpetion('remove_star @ reaction_remove, %s[cid=%d] %s[gid=%d]',
                          channel.name, channel.id,
                          channel.guild.name, channel.guild.id)

    async def on_raw_reaction_clear(self, message_id, channel_id):
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        cfg = await self.get_starconfig(channel.guild.id)
        if not cfg:
            return

        message = await channel.get_message(message_id)
        try:
            await self.remove_all(message, cfg)
        except (StarError, StarRemoveError) as err:
            log.warning(f'raw_reaction_clear: {err!r}')
        except Exception:
            log.excpetion('remove_all @ reaction_clear, %s[cid=%d] %s[gid=%d]',
                          channel.name, channel.id,
                          channel.guild.name, channel.guild.id)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def starboard(self, ctx, channel_name: str):
        """Create a starboard channel.
        
        If the name specifies a NSFW channel, the starboard gets marked as NSFW.

        NSFW starboards allow messages from NSFW channels to be starred without any censoring.
        If your starboard gets marked as a SFW starboard, messages from NSFW channels get completly ignored.
        """

        guild = ctx.guild
        config = await self.get_starconfig(guild.id)
        if config is not None:
            await ctx.send("You already have a starboard. If you want"
                           " to detach josé from it, use the "
                           "`stardetach` command")
            return

        po = discord.PermissionOverwrite
        overwrites = {
                guild.default_role: po(read_messages=True, send_messages=False),
                guild.me: po(read_messages=True, send_messages=True),
        }

        try:
            starboard_chan = await guild.create_text_channel(
                channel_name,
                overwrites=overwrites,
                reason='Created starboard channel')

        except discord.Forbidden:
            return await ctx.send('No permissions to make a channel.')
        except discord.HTTPException as err:
            log.exception('Got HTTP error from starboard create')
            return await ctx.send(f'**SHIT!!!!**:  {err!r}')

        log.info(f'[starboard] Init starboard @ {guild.name}[{guild.id}]')

        # create config here
        config = empty_starconfig(guild)
        config['starboard_id'] = starboard_chan.id

        res = await self.starconfig_coll.insert_one(config)
        if not res.acknowledged:
            raise self.SayException('Failed to create starboard config (no ack)')

        await ctx.send('All done, I guess!')

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def starattach(self, ctx, starboard_chan: discord.TextChannel):
        """Attach an existing channel as a starboard.

        With this command you can create your starboard
        without needing José to automatically create the starboard for you
        """
        config = await self.get_starconfig(ctx.guild.id)
        if config:
            return await ctx.send('You already have a starboard config setup.')

        config = empty_starconfig(ctx.guild)
        config['starboard_id'] = starboard_chan.id
        res = await self.starconfig_coll.insert_one(config)

        if not res.acknowledged:
            raise self.SayException('Failed to create starboard config (no ack)')
            return

        await ctx.send('Done!')
        await ctx.ok()

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def stardetach(self, ctx, confirm: str = 'n'):
        """Detaches José from your starboard.

        Detaching means José will remove your starboard's configuration.
        And will stop detecting starred/unstarred posts, etc.

        Provide "y" as your confirmation.

        Manage Guild permission is required.
        """
        if confirm != 'y':
            return await ctx.send('Operation not confirmed by user.')

        config = await self._get_starconfig(ctx.guild.id)
        await ctx.success(await self.delete_starconfig(config))

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def stardelete(self, ctx, confirm: str = 'n'):
        """Completly delete all starboard data from the guild.

        Follows the same logic as `j!stardetach`, but it
        deletes all starboard data, not just the configuration.
        """
        if confirm != 'y':
            return await ctx.send('not confirmed')

        config = await self._get_starconfig(ctx.guild.id)
        await self.delete_starconfig(config)

        self.loop.create_task(self.janitor_task(ctx.guild.id))
        await ctx.send('Data deletion scheduled.')

    @commands.command()
    @commands.guild_only()
    async def star(self, ctx, message_id: int):
        """Star a message."""
        try:
            message = await ctx.channel.get_message(message_id)
        except discord.NotFound:
            return await ctx.send('Message not found')
        except discord.Forbidden:
            return await ctx.send("Can't retrieve message")
        except discord.HTTPException as err:
            return await ctx.send(f'Failed to retrieve message: {err!r}')

        try:
            await self.add_star(message, ctx.author)
            await ctx.ok()
        except (StarAddError, StarError) as err:
            log.warning(f'[star_command] Errored: {err!r}')
            return await ctx.send(f'Failed to add star: {err!r}')

    @commands.command()
    @commands.guild_only()
    async def unstar(self, ctx, message_id: int):
        """Unstar a message."""
        try:
            message = await ctx.channel.get_message(message_id)
        except discord.NotFound:
            return await ctx.send('Message not found')
        except discord.Forbidden:
            return await ctx.send("Can't retrieve message")
        except discord.HTTPException as err:
            return await ctx.send(f'Failed to retrieve message: {err!r}')

        try:
            await self.remove_star(message, ctx.author)
            await ctx.ok()
        except (StarRemoveError, StarError) as err:
            log.warning(f'[unstar_cmd] Errored: {err!r}')
            return await ctx.send(f'Failed to remove star: {err!r}')

    @commands.command()
    @commands.guild_only()
    async def starrers(self, ctx, message_id: int):
        """Get the list of starrers from a message in the current channel."""
        try:
            message = await ctx.channel.get_message(message_id)
        except discord.NotFound:
            return await ctx.send('Message not found')
        except discord.Forbidden:
            return await ctx.send("Can't retrieve message")
        except discord.HTTPException as err:
            return await ctx.send(f'Failed to retrieve message: {err!r}')

        guild = ctx.guild
        await self._get_starconfig(guild.id)
        star = await self.get_star(guild.id, message.id)
        if star is None:
            return await ctx.send('Star object not found')

        _, em = make_star_embed(star, message)
        starrers = [guild.get_member(starrer_id)
                    for starrer_id in star['starrers']]

        em.add_field(name='Starrers', value=', '.join([m.display_name
                                                       for m in starrers]))
        await ctx.send(embed=em)

    @commands.command()
    @commands.guild_only()
    async def starstats(self, ctx):
        """Get statistics about your starboard."""
        guild = ctx.guild
        await self._get_starconfig(guild.id)

        em = discord.Embed(title='Starboard statistics',
                           colour=discord.Colour(0xFFFF00))

        total_stars = await self.starboard_coll.find({'guild_id': guild.id}).count()
        em.add_field(name='Total messages starred', value=total_stars)

        starrers = collections.Counter()
        # message with most stars
        max_message = [0, None, None]

        guild_stars = self.starboard_coll.find({'guild_id': guild.id})
        async for star in guild_stars:
            _starrers = star['starrers']
            if len(_starrers) > max_message[0]:
                max_message = [len(_starrers), star['message_id'],
                               star['channel_id']]

            for starrer_id in star['starrers']:
                starrers[starrer_id] += 1

        mm = max_message
        em.add_field(name='Most starred message',
                     value=f'{mm[0]} Stars, ID {mm[1]} on <#{mm[2]}>')

        # most_common is list of tuple (member_id, starcount)
        most_common = starrers.most_common(3)

        for idx, data in enumerate(most_common):
            member_id, star_count = data
            member = guild.get_member(member_id)
            if member is None:
                continue

            em.add_field(name=f'Starrer #{idx+1}',
                         value=f'{member.mention} with {star_count} stars')

        await ctx.send(embed=em)

    @commands.command(aliases=['rs'])
    @commands.guild_only()
    async def randomstar(self, ctx):
        """Get a random star from your starboard."""
        guild = ctx.guild
        all_stars = await self.starboard_coll.find({'guild_id': guild.id}).count()
        random_idx = random.randint(0, all_stars)
        
        guild_stars_cur = self.starboard_coll.find({'guild_id': guild.id}).limit(1).skip(random_idx)
        
        # ugly, I know.
        star = None
        async for star in guild_stars_cur:
            star = star

        if star is None:
            return await ctx.send('No star object found')

        channel = self.bot.get_channel(star['channel_id'])
        if channel is None:
            return await ctx.send('Star references a non-findable channel.')

        message_id = star['message_id']
        try:
            message = await channel.get_message(message_id)
        except discord.NotFound:
            raise self.SayException('Message not found')
        except discord.Forbidden:
            raise self.SayException("Can't retrieve message")
        except discord.HTTPException as err:
            raise self.SayException(f'Failed to retrieve message: {err!r}')

        current = ctx.channel.is_nsfw()
        schan = channel.is_nsfw()
        if not current and schan:
            raise self.SayException(f'channel nsfw={current}, nsfw={schan}, nope')

        title, embed = make_star_embed(star, message)
        await ctx.send(title, embed=embed)

    @commands.command()
    @commands.guild_only()
    async def streload(self, ctx, message_id: int):
        """Star reload.

        Reload a message, its starrers and update the star in the starboard.
        Useful if the starred message was edited.
        """
        channel = ctx.channel
        cfg = await self._get_starconfig(channel.guild.id)

        try:
            message = await channel.get_message(message_id)
        except discord.NotFound:
            raise self.SayException('message not found')

        star = await self.get_star(ctx.guild.id, message_id)
        if star is None:
            raise self.SayException('star object not found')

        try:
            await self.update_star(cfg, star, msg=message)
        except StarError as err:
            log.error(f'force_reload: {err!r}')
            raise self.SayException(f'rip {err!r}')

        await ctx.ok()


def setup(bot):
    bot.add_cog(Starboard(bot))
