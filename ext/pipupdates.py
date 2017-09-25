#!/usr/bin/env python3

import subprocess
import asyncio
import logging

from .common import Cog
from discord.ext import commands

log = logging.getLogger(__name__)

def pip_freeze():
    out = subprocess.check_output('pip freeze', shell=True)
    return out


class PipUpdates(Cog):
    def __init__(self, bot):
        super().__init__(bot)

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

        self.update_task = self.bot.loop.create_task(self.update_task_func())

    def __unload(self):
        self.update_task.cancel()

    async def update_task_func(self):
        try:
            while True:
                await self.checkupdates()
                await asyncio.sleep(21600)
        except asyncio.CancelledError:
            pass

    async def checkupdates(self):
        future_pip = self.bot.loop.run_in_executor(None, pip_freeze)
        out = await future_pip
        out = out.decode('utf-8')
        packages = out.split('\n')

        res = []

        for pkgline in packages:
            print('working on freeze pkgline', pkgline)

            r = pkgline.split('==')
            if len(r) != 2:
                continue
            pkgname = r[0]

            print('in requirements?', pkgname in self.requirements)
            if pkgname in self.requirements:
                cur_version = self.requirements[pkgname]

                print('requesting', f'http://pypi.python.org/pypi/{pkgname}/json')
                pkgdata = await self.get_json(f'http://pypi.python.org/pypi/{pkgname}/json')

                new_version = pkgdata['info']['version']
                log.info('[pip] checking %s: current=%s against latest=%s',
                         pkgname, cur_version, new_version)

                if new_version != cur_version:
                    log.info('[pip] New update for %s', pkgname)
                    res.append(" * `%r` needs update from %s to %s" % \
                        (pkgname, cur_version, new_version))

        print('result is', res)
        await self.say_results(res)
        return res

    async def say_results(self, res):
        if len(res) <= 0:
            return

        owner = (await self.bot.application_info()).owner
        res.insert(0, ':alarm_clock: You have package updates :alarm_clock:')
        await owner.send('\n'.join(res))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def checkpkgs(self, ctx):
        """Query PyPI for new package updates."""
        async with ctx.typing():
            res = await self.checkupdates()

            if len(res) <= 0:
                return await ctx.send("`No updates found.`")

            await ctx.send('Updates were found and should be sent to the bot owner!')

def setup(bot):
    bot.add_cog(PipUpdates(bot))
