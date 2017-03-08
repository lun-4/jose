#!/usr/bin/env python3

import subprocess
import sys
sys.path.append("..")
import jauxiliar as jaux
import josecommon as jcommon
import joseerror as je

def pip_freeze():
    out = subprocess.check_output('pip freeze', shell=True)
    return out

class JoseWatch(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)
        self.watch = {}
        self.requirements = {}

        reqlist = None
        with open('requirements.txt', 'r') as reqfile:
            reqlist = (reqfile.read()).split('\n')

        for pkg in reqlist:
            r = pkg.split('==')
            if len(r) != 2:
                continue
            pkgname, pkgversion = r[0], r[1]
            self.requirements[pkgname] = pkgversion

        self.cbk_new('jwatch.updates', self.checkupdates, 3600)

    async def ext_load(self):
        return True, ''

    async def ext_unload(self):
        return True, ''

    async def checkupdates(self):
        future_pip = self.loop.run_in_executor(None, pip_freeze)
        out = await future_pip
        out = out.decode('utf-8')
        packages = out.split('\n')

        res = []

        for pkgline in packages:
            pkgname, pkgversion = pkgline.split('==')

            if pkgname in self.requirements:
                cur_version = self.requirements[pkgname]

                # :^)
                if pkgname == 'discord.py[voice]':
                    pḱgname = 'discord.py'

                pkgdata = await self.json_from_url('http://pypi.python.org/pypi/{}/json'.format\
                    (pkgname))

                new_version = pkgdata['info']['version']
                if new_version != cur_version:
                    # !!!!!
                    res.append(" * `%r` needs update from %s to %s" % \
                        (pkgname, curversion, pkgversion))

        await self.say_results(res)
        return res

    async def say_results(self, res):
        if len(res) <= 0:
            return

        res_str = '\n'.join(res)

        em = discord.Embed(title='NEW UPDATES')
        for string in res_str:
            em.add_field(name='', value='{}'.format(string))

        em.set_footer(text="Total of {} updates".format(len(res)))

        jose_dev_server = [server for server in self.client.servers \
            if server.id == jcommon.JOSE_DEV_SERVER_ID][0]

        channel = discord.utils.get(jose_dev_server.channels, name='chat')

        await self.client.send_message(channel, embed=em)

    async def c_checkpkgs(self, message, args, cxt):
        await self.is_admin(cxt.message.author.id)
        res = await self.checkupdates()

        if len(res) < 0:
            await cxt.say("`No updates found.`")

        return
