#!/usr/bin/env python3

import sys
sys.path.append("..")
import jauxiliar as jaux
import josecommon as jcommon
import discord
import datetime

MARKDOWN_HELP_FILES = [
    'doc/cmd/listcmd.md',
    'doc/cmd/admin.md',
    'doc/josespeak.md',
    'doc/jcoin.md'
]

JOSE_INVITE = 'https://discord.gg/5ASwg4C'
JOSE_LISTCMD_URL = 'https://github.com/lkmnds/jose/blob/master/doc/cmd/listcmd.md'
FEEDBACK_CHANNEL_ID = '290244095820038144'

class JoseHelp(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)
        self.help = {}

    def load_helpfiles(self):
        for file in MARKDOWN_HELP_FILES:
            with open(file, 'r') as f:
                # do I really need to parse MARKDOWN, without libs?
                for line in f.readlines():
                    if line.find('|'):
                        data = [sp.strip() for sp in line.split('|')]
                        if len(data) == 4:
                            raw_cmd = data[0]
                            c = raw_cmd.find('`')
                            a_cmd = raw_cmd[c+1:raw_cmd.find('`', c+1)]
                            a_cmd = a_cmd.split()
                            cmd = '`%s`' % (a_cmd[0])
                            desc = data[1]
                            examples = data[2]
                            aliases = data[3]

                            self.help[cmd] = {
                                'description': desc,
                                'examples': examples,
                                'aliases': aliases
                            }

    async def ext_load(self):
        self.load_helpfiles()
        return True, ''

    async def ext_unload(self):
        del self.help
        return True, ''

    async def c_helpme(self, message, args, cxt):
        '''`j!helpme` - having problems?'''

        if message.server.id != jcommon.JOSE_DEV_SERVER_ID:
            em = discord.Embed(title="Having Problems?", colour=discord.Colour.red())
            em.add_field(name="José server: ", value="{}".format(JOSE_INVITE))
            em.add_field(name="what do", value="Use `j!helpme` there and find the nearest mod that works with your issue")
            await cxt.say_embed(em)
            return

        res = []

        for adminid in jcommon.ADMIN_TOPICS:
            topics = jcommon.ADMIN_TOPICS[adminid]
            admin = message.server.get_member(adminid)
            if admin.status == discord.Status.online:
                res.append(":green_book: %s, works on %s" % (admin, ', '.join(topics)))
            elif admin.status == discord.Status.idle:
                res.append(":white_circle: %s, works on %s" % (admin, ', '.join(topics)))
            elif admin.status == discord.Status.dnd:
                res.append(":red_circle: %s, works on %s" % (admin, ', '.join(topics)))
            else:
                # admin is Offline, don't show them lol
                pass

        if len(res) == 0:
            await cxt.say("Sorry, no admin is available to treat your issue.")
            return

        await cxt.say('\n'.join(res))

    async def c_help(self, message, args, cxt):
        '''`j!help` - send list of commands to you'''
        await cxt.say("Use `j!helpcmd` for single command help. \n{}".format\
            (JOSE_LISTCMD_URL))

    async def c_helpcmd(self, message, args, cxt):
        '''`j!helpcmd cmd` - get help for a command, uses the Markdown documentation'''
        if len(args) < 2:
            await cxt.say(self.c_helpcmd.__doc__)
            return

        command = args[1]

        # thats ugly, just... ugly.
        command = '`j!%s`' % command

        if command in self.help:
            res = []
            helpdata = self.help[command]

            res.append("Command: `%s`" % command)
            res.append("**Description**: %s" % helpdata['description'])
            res.append("Example: %s" % helpdata['examples'])
            res.append("Aliases: %s" % helpdata['aliases'])

            await cxt.say('\n'.join(res))
        else:
            await cxt.say("No helptext was found for `%s`, try `j!docstring`", (command,))
        return

    async def c_docstring(self, message, args, cxt):
        '''`j!docstring command` - get the docstring for that command'''

        # load helptext
        cmd_ht = 'docstring'
        try:
            if args[1] == 'docstring':
                await cxt.say(self.c_docstring.__doc__)
                return
            else:
                cmd_ht = args[1]
        except:
            pass

        if cmd_ht == 'docstring':
            await cxt.say(self.c_docstring.__doc__)
            return

        cmd_method = getattr(cxt.jose, 'c_%s' % cmd_ht, None)
        if cmd_method is None:
            await cxt.say("%s: Command not found" % cmd_ht)
            return

        try:
            docstring = cmd_method.__doc__
            if docstring is None:
                await cxt.say("Command found, docstring not found")
            else:
                await cxt.say(docstring)
        except Exception as e:
            await cxt.say("Error getting docstring for %s: %r" % (cmd_ht, repr(e)))

    async def c_feedback(self, message, args, cxt):
        '''`j!feedback stuff` - Sends feedback'''

        em = discord.Embed(title='', colour=discord.Colour.magenta())
        em.timestamp = datetime.datetime.now()
        em.set_footer(text='Feedback Report')
        em.set_author(name=str(member), icon_url=member.avatar_url or member.default_avatar_url)

        channel = message.channel
        server = message.server

        em.add_field(name="Feedback: ", value=feedback)
        em.add_field(name="Server", value="{} [{}]".format(server.name, server.id))
        em.add_field(name="Channel", value="{} [{}]".format(channel.name, channel.id))

        feedback_channel = self.client.get_channel(FEEDBACK_CHANNEL_ID)
        await cxt.say_embed(em, feedback_channel)
