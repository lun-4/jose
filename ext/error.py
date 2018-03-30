import logging
import collections

from discord.ext import commands
from .common import Cog

log = logging.getLogger(__name__)


class ErrorHandling(Cog):
    async def on_command_error(self, ctx, error):
        """Log and signal errors to the user"""
        message = ctx.message
        content = self.bot.clean_content(message.content)

        # TODO: I get the feeling this function is too long,
        #   We have too many branches.
        #   Can we make this cleaner?

        if isinstance(error, commands.errors.CommandInvokeError):
            orig = error.original

            if isinstance(orig, self.SayException):
                arg0 = orig.args[0]

                if ctx.guild is None:
                    dm = collections.namedtuple('DM', 'id')
                    ctx.guild = dm(ctx.author.id)

                log.warning('SayException: %s[%d] %s %r => %r', ctx.guild,
                            ctx.guild.id, ctx.author, content, arg0)

                return await ctx.send(arg0)

            if isinstance(orig, tuple(self.bot.simple_exc)):
                log.error(f'Errored at {content!r} from {ctx.author!s}'
                          f'\n{orig!r}')
                return await ctx.send(f'Error: `{error.original!r}`')
            else:
                log.exception(f'Errored at {content!r} from {ctx.author!s}',
                              exc_info=orig)

            if isinstance(orig, self.bot.cogs['Coins'].TransferError):
                return await ctx.send(f'JoséCoin error: `{orig!r}`')

            return await ctx.send('An error happened during command exeuction:'
                                  f'```py\n{error.original!r}```')

        if isinstance(error, commands.errors.BadArgument):
            return await ctx.send('bad argument —  '
                                  f'{error!s}')

        if isinstance(error, commands.errors.CommandOnCooldown):
            return

        if isinstance(error, commands.errors.MissingRequiredArgument):
            return await ctx.send(f'missing argument — `{error.param}`')
        if isinstance(error, commands.errors.NoPrivateMessage):
            return await ctx.send('sorry, you can not use this command'
                                  ' in a DM.')
        if isinstance(error, commands.errors.UserInputError):
            return await ctx.send('user input error  — '
                                  'please, the *right* thing')

        if isinstance(error, commands.errors.MissingPermissions):
            join = ', '.join(error.missing_perms)
            return await ctx.send(f'user is missing permissions — `{join}`')
        if isinstance(error, commands.errors.BotMissingPermissions):
            join = ', '.join(error.missing_perms)
            return await ctx.send(f'bot is missing permissions — `{join}`')

        # we put this one because MissingPermissions might be a
        # disguised CheckFailure
        if isinstance(error, commands.errors.CheckFailure):
            checks = [c.__qualname__.split('.')[0] for c in ctx.command.checks]
            await ctx.err(f'check error — checks: `{", ".join(checks)}`')


def setup(bot):
    bot.add_cog(ErrorHandling(bot))
