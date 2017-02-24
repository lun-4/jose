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
