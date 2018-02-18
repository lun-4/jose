#!/usr/bin/env python3

import sys
import os
import operator
import time

sys.path.append("..")
import jauxiliar as jaux
import josecommon as jcommon
import joseconfig as jconfig

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
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)
        self.statistics = {}
        self.jose = self.client.jose

        # every 2 minutes, save databases
        self.cbk_new('jstats.savedb', self.savedb, 180)
        self.cbk_new('jstats.timestamped', self.stats_timestamp, 600)

    async def savedb(self):
        try:
            self.logger.debug("savedb:stats")
            await self.jsondb_save_all()
        except Exception as err:
            self.logger.error("[statsdb] error saving: %r", err, exc_info=True)

    async def ext_load(self):
        try:
            self.jsondb('statistics', path=jcommon.STAT_DATABASE_PATH, \
                default=DEFAULT_STATS_FILE)

            self.jsondb('timed_stats', path='db/timed_stats.json')

            # make sure i'm making sane things
            # also make the checks in ext_load (instead of any_message)
            # so it doesn't fry the cpu
            if 'gl_messages' not in self.statistics:
                self.statistics['gl_messages'] = 0

            if 'gl_commands' not in self.statistics:
                self.statistics['gl_commands'] = {}

            if 'gl_queries' not in self.statistics:
                self.statistics['gl_queries'] = 0

            return True, ''
        except Exception as err:
            return False, str(err)

    async def ext_unload(self):
        try:
            # save databases
            await self.savedb()

            # Remove the callback
            self.cbk_remove('jstats.savedb')

            return True, ''
        except Exception as err:
            return False, str(err)

    async def db_fsizes(self):
        return {
            'jspeak:database': os.path.getsize(jcommon.JOSE_DATABASE_PATH),
            'jspeak:word_length': os.path.getsize(jcommon.MARKOV_LENGTH_PATH),
            'jspeak:message_count': os.path.getsize(jcommon.MARKOV_MESSAGES_PATH),
            'jstats:statistics': os.path.getsize(jcommon.STAT_DATABASE_PATH),
            'jmword:magicword': os.path.getsize(jconfig.MAGICWORD_PATH),
            'jlang:configdb': os.path.getsize(jcommon.CONFIGDB_PATH),
        }

    async def c_saveqdb(self, message, args, cxt):
        await self.savedb()
        await cxt.say(":floppy_disk: saved query database :floppy_disk:")

    async def stats_timestamp(self):
        timestamp = time.time()

        g_cmd = self.statistics['gl_commands']
        sorted_gcmd = sorted(g_cmd.items(), \
            key=operator.itemgetter(1), reverse=True)

        t1 = time.monotonic()
        logging_ch = self.client.get_channel(jcommon.JOSE_LOG_CHANNEL_ID)
        if logging_ch is not None:
            await self.client.send_typing(logging_ch)
            t2 = time.monotonic()
            typing_ping = t2 - t1
        else:
            # make errors *almost* obvious to the graph
            typing_ping = -0.2

        jose = self.jose

        self.timed_stats[timestamp] = [
            # num of messages received
            self.statistics['gl_messages'],

            # total commands done
            sum(self.statistics['gl_commands'].values()),

            # top10 most used commands
            sorted_gcmd[:10],

            # ping to send a typing status
            typing_ping,

            # message more like meme
            jose.msgcount_min,
            jose.msgcount_hour,

            jose.best_msg_minute,
            jose.best_msg_hour,

            jose.total_msg,

            # total socket events
            sum(jose.socket_stats.values()),
        ]

        self.jsondb_save('timed_stats')

    async def e_any_message(self, message, cxt):
        if message.server is None:
            return

        serverid = message.server.id
        authorid = message.author.id

        if serverid not in self.statistics:
            self.logger.info("New server in statistics: %s", serverid)
            self.statistics[serverid] = {
                "commands": {},
                "messages": {}
            }

        # USE AS REFERENCE TO READ, NOT TO WRITE
        serverdb = self.statistics[serverid]

        if authorid not in serverdb['messages']:
            self.statistics[serverid]['messages'][authorid] = 0

        command, args, method = jcommon.parse_command(message.content)

        if command:
            if command not in serverdb['commands']:
                self.statistics[serverid]['commands'][command] = 0

            if command not in self.statistics['gl_commands']:
                self.statistics['gl_commands'][command] = 0

            self.statistics[serverid]['commands'][command] += 1
            self.statistics['gl_commands'][command] += 1
        else:
            # normal message
            # serverdb['messages'][authorid] => number of messages
            self.statistics[serverid]['messages'][authorid] += 1
            self.statistics['gl_messages'] += 1

    async def e_server_remove(self, server):
        server_id = server.id
        self.logger.info("Removed from server %s[%s]", server.name, server_id)

        # TODO: Removal

    async def c_query(self, message, args, cxt):
        '''`j!query data` - Query some statistics
https://github.com/lkmnds/jose/blob/master/doc/queries-pt.md'''

        if len(args) < 2:
            await cxt.say(self.c_query.__doc__)

        querytype = ' '.join(args[1:])
        response = ''

        self.statistics['gl_queries'] += 1

        if querytype == 'summary':
            # Because `josestats` came AFTER `josespeak`, the Texter calculation
            # was off by 7931 messages from the `josestats` calculation
            # this fixes it, i suppose
            response += "Messages received: %d\n" % (self.statistics['gl_messages'] + 7931)
            response += "Commands done: %d\n" % sum(self.statistics['gl_commands'].values())
            response += "Queries made: %d\n" % self.statistics['gl_queries']

            # calculate most used command
            sorted_gcmd = sorted(self.statistics['gl_commands'].items(), \
                key=operator.itemgetter(1))

            if len(sorted_gcmd) > 1:
                most_used_commmand = sorted_gcmd[-1][0]
                muc_uses = sorted_gcmd[-1][1]
                response += "Most used command: %s, used %d times\n" % \
                    (most_used_commmand, muc_uses)

        elif querytype == 'dbsize':
            sizes = await self.db_fsizes()
            for db in sorted(sizes):
                sizes[db] = '%.3f' % (sizes[db] / 1024)
            response = "\n".join(": ".join(_) + "KB" for _ in sizes.items())
        elif querytype == 'this':
            if message.server.id is None:
                await cxt.say("`j!query this` not available for DMs")
                return

            sdb = self.statistics[message.server.id]

            total_msg = 0
            for authorid in sdb['messages']:
                total_msg += sdb['messages'][authorid]

            response += "Messages from this server: %d\n" % total_msg
            response += "Commands from this server: %d\n" % sum(sdb['commands'].values())

            # calculate most used command
            sorted_gcmd = sorted(sdb['commands'].items(), \
                key=operator.itemgetter(1))

            if len(sorted_gcmd) > 1:
                most_used_commmand = sorted_gcmd[-1][0]
                muc_uses = sorted_gcmd[-1][1]
                response += "Most used command from this server: %s, used %d times\n" % \
                    (most_used_commmand, muc_uses)

        elif querytype == 'topcmd':
            g_cmd = self.statistics['gl_commands']
            sorted_gcmd = sorted(g_cmd.items(), \
                key=operator.itemgetter(1), reverse=True)

            response = '\n'.join(['%s - %d times' % \
                (x, y) for (x, y) in sorted_gcmd[:10]])
        elif querytype == 'ltopcmd':
            if message.server.id is None:
                await cxt.say("`j!query ltopcmd` not available for DMs")
                return

            sdb = self.statistics[message.server.id]
            sorted_gcmd = sorted(sdb['commands'].items(), \
                key=operator.itemgetter(1), reverse=True)

            response = '\n'.join(['%s - %d times' % \
                (x, y) for (x, y) in sorted_gcmd[:10]])

        else:
            await cxt.say("Query type not found")
            return

        if len(response) >= 2000:
            await cxt.say(":elephant: big results :elephant:")
        else:
            await cxt.say(self.codeblock("", response))
