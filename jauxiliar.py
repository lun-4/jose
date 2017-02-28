#!/usr/bin/env python3

'''
jauxiliar.py - Auxiliar stuff for Jose modules
'''

import josecommon as jcommon
import jcoin.josecoin as jcoin
import joseerror as je
import json
import aiohttp

class Auxiliar(jcommon.Extension):
    '''
    Auxiliar - auxiliar functions and modules
    All modules that inherit from this class have access to things that wouldn't
    be possible if they were inheriting from jcommon.Extension.

    For example josecoin, josecoin imports from josecommon, but if josecommon
    imported josecoin into its Extension class, it would make a circular import.
    '''
    def __init__(self, client):
        jcommon.Extension.__init__(self, client)
        self.jcommon = jcommon
        self.jcoin = jcoin

    async def jc_control(self, id_user, amnt, ledger_path=None):
        return jcoin.transfer(id_user, jcoin.jose_id, amnt, ledger_path)

    async def json_load(self, string):
        future_json = self.loop.run_in_executor(None, json.loads, string)

        try:
            res = await future_json
        except Exception as err:
            raise je.CommonError("Error parsing JSON data")

        return res

    async def json_from_url(url):
        resp = await aiohttp.request('GET', url)
        content = await resp.text()
        data = await self.json_load(content)
        return data
