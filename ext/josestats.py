#!/usr/bin/env python3

import discord
import asyncio
import sys
import json
import os

sys.path.append("..")
import jauxiliar as jaux
import joseerror as je
import josecommon as jcommon

class JoseStats(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)
        self.statistics = {}
        self.db_stats_path = jcommon.STAT_DATABASE_PATH
        self.counter = 0

    async def savedb(self):
        json.dump(self.statistics, open(self.db_stats_path, 'w'))

    async def ext_load(self):
        try:
            self.statistics = {}
            self.database = json.load(open(self.db_stats_path, 'r'))
            return True, ''
        except Exception as e:
            return False, str(e)

    async def ext_unload(self):
        try:
            await self.savedb()
            return True, ''
        except Exception as e:
            return False, str(e)

    async def db_fsizes(self):
        return {
            'markovdb': os.path.getsize(jcommon.MARKOV_DB_PATH),
            'wlength': os.path.getsize(jcommon.MARKOV_LENGTH_PATH),
            'messages': os.path.getsize(jcommon.MARKOV_MESSAGES_PATH),
            'itself': os.path.getsize(jcommon.STAT_DATABASE_PATH),
        }

    async def e_any_message(self, message):
        serverid = message.server.id
        authorid = message.author.id
        channel = message.channel.id

        if serverid not in self.statistics:
            self.statistics[serverid] = {
                "commands": {},
                "messages": {}
            }

        serverdb = self.statistics[serverid]

        if self.counter % 50 == 0:
            await self.savedb()

        command, args, method = jcommon.parse_command(message.content)

        if authorid not in serverdb['messages']:
            serverdb['messages'][authorid] = [0, 0]

        if not command:
            # normal message, calculate average wordlength for this user
            # serverdb['messages'][authorid][0] => number of messages
            # serverdb['messages'][authorid][1] => combined wordlength of all messages
            serverdb['messages'][authorid][0] += 1
            serverdb['messages'][authorid][1] += len(message.content.split())
        else:
            # command
            if command not in serverdb['commands']:
                serverdb['commands'][command] = 0

            serverdb['commands'][command] += 1

        self.counter += 1

    async def c_querysiz(self, message, args):
        '''`!querysiz` - Mostra os tamanhos dos bancos de dados do josé, em kilobytes(KB)'''
        sizes = await self.db_fsizes()
        res = "\n".join(": ".join(_) for _ in sizes.items())
        await self.say(self.codeblock("", res))

    async def c_query(self, message, args):
        '''`!query string` - Fazer pedidos ao banco de dados de estatísticas do josé'''
        query_string = ' '.join(args[1:])
        if True:
            await self.say("not available for now")
            return

        # TODO: make_query
        response = await self.make_query(query_string)
        if len(response) > 1999: # 1 9 9 9
            await self.say(":elephant: Resultado muito grande :elephant:")
        else:
            await self.say(self.codeblock("", reponse))
