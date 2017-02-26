#!/usr/bin/env python3

'''
jauxiliar.py - Auxiliar stuff for Jose modules
'''

import josecommon as jcommon
import jcoin.josecoin as jcoin

class Auxiliar(jcommon.Extension):
    def __init__(self, cl):
        jcommon.Extension.__init__(self, cl)
        self.jcommon = jcommon
        self.jcoin = jcoin

    async def jc_control(self, id_user, amnt, ledger_path=None):
        return jcoin.transfer(id_user, jcoin.jose_id, amnt, ledger_path)
