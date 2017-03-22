#!/usr/bin/env python3

import discord
import io
import traceback
import contextlib
import textwrap
import sys
sys.path.append("..")
import jauxiliar as jaux

class JoseTools(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)
        self._last_res = None

    async def ext_load(self):
        try:
            return True, ''
        except Exception as err:
            return False, repr(err)

    async def ext_unload(self):
        try:
            return True, ''
        except Exception as err:
            return False, repr(err)

    def rm_codeblocks(self, content):
        # yeah, got it from RoboDanny.
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        return content.strip('` \n')

    def debug_err(self, out_data, traceback_err):
        return self.codeblock('py', f'err: {traceback_err}\noutput: {out_data}')

    async def c_debug(self, message, args, cxt):
        await self.is_admin(cxt.message.author.id)

        enviroment = {
            'modules': self.client.jose.modules,
            'jose': self.client.jose,
            'cl': self.client,
            'msg': message,
            'author': cxt.author,
            'server': cxt.server,
            'channel': cxt.channel,
            'me': cxt.me,
            'res': self._last_res,
        }

        enviroment.update(globals())

        debug_input = self.rm_codeblocks(' '.join(args[1:]))
        debug_input = textwrap.indent(debug_input, '  ')
        code = f'async def debug():\n{debug_input}'

        try:
            exec(code, enviroment)
        except Exception as err:
            await cxt.say(self.codeblock('', traceback.format_exc()))
            return

        output = io.StringIO()
        debug = enviroment['debug']
        try:
            with contextlib.redirect_stdout(output):
                retval = await debug()
        except Exception as err:
            out_data = output.getvalue()
            await cxt.say(self.debug_err(out_data, traceback.format_exc()))
            return

        out_data = output.getvalue()
        self._last_res = retval
        f_retval = repr(retval)
        await cxt.say(self.codeblock('py', f'out:\n {out_data}\nres:\n {f_retval}'))
