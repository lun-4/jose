#!/usr/bin/env python3

import sys
sys.path.append("..")
import jauxiliar as jaux

MARKDOWN_HELP_FILES = [
    'doc/cmd/listcmd.md',
    'doc/cmd/admin.md',
    'doc/josespeak.md',
    'doc/jcoin.md'
]

class JoseHelp(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)
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

            res.append("Command: `%s`" % command)
            res.append("**Description**: %s" % helpdata['description'])
            res.append("Example: %s" % helpdata['examples'])
            res.append("Aliases: %s" % helpdata['aliases'])

            await cxt.say('\n'.join(res))
        else:
            await cxt.say("No helptext was found for `%s`, try `j!docstring`", (command,))
        return
