#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import jauxiliar as jaux

MARKDOWN_HELP_FILES = [
    'doc/cmd/listcmd.md',
    'doc/josespeak.md',
]

class JoseExtension(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)
        self.help = {}

    def load_helpfiles():
        for file in MARKDOWN_HELP_FILES:
            with open(file, 'r') as f:
                # do I really need to parse MARKDOWN, without libs?
                for line in f.readlines():
                    if line.find('|'):
                        data = line.split('|')
                        cmd = data[0].strip()
                        desc = data[1].strip()
                        examples = data[2].strip()
                        aliases = data[3].strip()

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

    async def c_help(self, message, args, cxt):
        '''`j!help cmd` - get help for a command, uses the Markdown helptexts'''
        if len(args) < 2:
            await cxt.say(self.c_help.__doc__)
            return

        command = args[1]

        # thats ugly, just... ugly.
        command = '`j!%s`' % command

        if command in self.help:
            res = []
            helpdata = self.help[command]

            res.append("Command: `j!%s`" % command)
            res.append("**Description**: `%s`" % helpdata['description'])
            res.append("Example: `%s`" % helpdata['examples'])
            res.append("Aliases: `%s`" % helpdata['aliases'])

            await cxt.say('\n'.join(res))
        else:
            await cxt.say("No helptext was found for `j!%s`, try `j!docstring`", (command,))
        return
