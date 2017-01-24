#!/usr/bin/env python3

import discord
import asyncio
import sys
import json
import os
import operator

sys.path.append("..")
import jauxiliar as jaux
import joseerror as je
import josecommon as jcommon

# TODO: query language
QUERIES = {
    "topmsg": "loc[msg].sort",
    "gltopcmd": "db[cmd].sort"
}

DEFAULT_STATS_FILE = '''{
    "gl_queries": 0,
    "gl_messages": 0,
    "gl_commands": {},
}'''

'''
    database format, json
    {
        "gl_queries": number of queries,
        "gl_commands": {
            "!savedb": 2
        }
        "gl_messages": number of messages
        "serverID1": {
            "commands": {
                '!m stat': 30,
                '!top10': 10
            },
            "messages": {
                "authorid1": [number of messages, total wordlength of all messages],
                "authorid2": [number of messages, total wordlength of all messages]
            }
        }
    }
'''

class JoseStats(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)
        self.statistics = {}
        self.db_stats_path = jcommon.STAT_DATABASE_PATH
        self.counter = 0

    async def savedb(self):
        self.logger.info("Saving statistics database")
        json.dump(self.statistics, open(self.db_stats_path, 'w'))

    async def ext_load(self):
        try:
            self.statistics = {}
            if not os.path.isfile(self.db_stats_path):
                # recreate
                with open(self.db_stats_path, 'w') as f:
                    f.write(DEFAULT_STATS_FILE)

            self.database = json.load(open(self.db_stats_path, 'r'))

            # make sure i'm making sane things
            # also make the checks in ext_load so it doesn't try the cpu
            if 'gl_messages' not in self.statistics:
                self.statistics['gl_messages'] = 0

            if 'gl_commands' not in self.statistics:
                self.statistics['gl_commands'] = {}

            if 'gl_queries' not in self.statistics:
                self.statistics['gl_queries'] = 0

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

    async def c_saveqdb(self, message, args):
        await self.savedb()
        await self.say(":floppy_disk: saved query database :floppy_disk:")

    async def e_any_message(self, message):
        serverid = message.server.id
        authorid = message.author.id
        channel = message.channel.id

        if serverid not in self.statistics:
            self.logger.info("New server in statistics: %s", serverid)
            self.statistics[serverid] = {
                "commands": {},
                "messages": {}
            }

        # USE AS REFERENCE, NOT TO WRITE
        # probably that's what caused the "query delay until reload"
        serverdb = self.statistics[serverid]

        if self.counter % 50 == 0:
            await self.savedb()

        command, args, method = jcommon.parse_command(message.content)

        if authorid not in serverdb['messages']:
            self.statistics[serverid]['messages'][authorid] = [0, 0]

        if not command:
            # normal message, calculate average wordlength for this user
            # serverdb['messages'][authorid][0] => number of messages
            # serverdb['messages'][authorid][1] => combined wordlength of all messages
            self.statistics[serverid]['messages'][authorid][0] += 1
            self.statistics[serverid]['messages'][authorid][1] += len(message.content.split())
            self.statistics['gl_messages'] += 1
        else:
            # command
            if command not in serverdb['commands']:
                self.statistics[serverid]['commands'][command] = 0

            if command not in self.statistics['gl_commands']:
                self.statistics['gl_commands'][command] = 0

            self.statistics[serverid]['commands'][command] += 1
            self.statistics['gl_commands'][command] += 1

        #self.statistics[serverid] = serverdb
        self.counter += 1

    async def c_rawquery(self, message, args):
        '''`!rawquery string` - Fazer pedidos ao banco de dados de estatísticas do josé'''
        query_string = ' '.join(args[1:])
        if True:
            await self.say("raw queries not available for now")
            return

        # TODO: make_query
        response = await self.make_raw_query(query_string)
        if len(response) > 1999: # 1 9 9 9
            await self.say(":elephant: Resultado muito grande :elephant:")
        else:
            await self.say(self.codeblock("", reponse))

    async def c_query(self, message, args):
        '''`!query data` - Fazer pedidos ao banco de dados de estatísticas do josé
A lista de possíveis dados está em https://github.com/lkmnds/jose/blob/master/doc/queries.md'''

        querytype = ' '.join(args[1:])
        response = ''

        self.database['gl_queries'] += 1

        if querytype == 'summary':
            response += "Total messages received: %d\n" % self.database['gl_messages']
            response += "Total queries done: %d\n" % self.database['gl_queries']

            # calculate most used command
            sorted_gcmd = sorted(self.database['gl_commands'].items(), key=operator.itemgetter(1))

            most_used_commmand = sorted_gcmd[-1][0]
            muc_uses = sorted_gcmd[-1][1]
            response += "Most used command: %s with %d uses\n" % (most_used_commmand, muc_uses)
        elif querytype == 'dbsize':
            sizes = await self.db_fsizes()
            for db in sizes:
                sizes[db] = '%.3f' % (sizes[db] / 1024)
            response = "\n".join(": ".join(_) + "KB" for _ in sizes.items())

        if len(response) > 1999: # 1 9 9 9
            await self.say(":elephant: Resultado muito grande :elephant:")
        else:
            await self.say(self.codeblock("", response))

    async def c_session(self, message, args):
        '''`!session` - Dados interessantes sobre essa sessão'''
        # uptime etc
