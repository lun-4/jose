#!/usr/bin/env python3

import time
import uuid
import sys
sys.path.append("..")
import jauxiliar as jaux

POLLID_MAX_TRIES = 10
POLL_ACTIONS = ['close', 'results']

def uniq():
    return str(uuid.uuid4().fields[-1])[:5]

class Polls(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)

        self.jsondb('polls', path='db/polls.json')

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

    def mkpoll_id(self):
        tries = 0
        new_id = uniq()
        while new_id in self.polls:
            if tries >= POLLID_MAX_TRIES:
                return None

            new_id = uniq()
            tries += 1

        return new_id

    async def c_mkpoll(self, message, args, cxt):
        '''`j!mkpoll title;op1;op2;...;opN` - create a poll'''

        # parse shit
        try:
            s = ' '.join(args[1:])
            if len(s.strip()) < 0:
                await cxt.say("error parsing your shit")
                return

            sp = s.split(';')
            if len(sp) < 2:
                await cxt.say("error parsing your shit")
                return

            title = sp[0]
            options = sp[1:]
        except:
            await cxt.say("Error parsing your shit!!!!!")
            return

        poll_id = self.mkpoll_id()
        if poll_id is None:
            self.logger.warning("[polls] CAN'T GENERATE MORE POLL IDS")
            await cxt.say(":warning: o shit, poll generation is flooded, `j!helpme` :warning:")
            return

        self.logger.info("[polls:%s] Created poll %r", poll_id, title)

        # create the poll
        self.polls[poll_id] = {
            'timestamp': time.time(),
            'closed': False,
            'owner': str(message.author.id),
            'title': title,
            'options': options,
            'votes': {},
        }

        await cxt.say(":ballot_box: Your Poll ID is `%s`", (poll_id,))

    async def c_poll(self, message, args, cxt):
        '''`j!poll poll_id action` - do a poll action(`close` for example, `results` as well)'''

        try:
            poll_id = args[1]
            action = args[2]
        except:
            await cxt.say("`j!poll poll_id action`.")
            return

        if poll_id not in self.polls:
            await cxt.say("Poll not found.")
            return

        if action not in POLL_ACTIONS:
            await cxt.say("Action not found.")
            return

        author_id = str(message.author.id)
        poll = self.polls[poll_id]
        if action == 'close':
            admin = await self.b_isowner(message.author.id)
            poll_owner = author_id == poll['owner']
            if not (poll_owner or admin):
                await cxt.say(':lock: Unauthorized :lock:')

            poll['closed'] = True
            await cxt.say("Poll closed with success.")
        elif action == 'results':
            votes = poll['votes']

            counts = {}
            for userid in votes:
                vote = votes['userid']

                if vote not in counts:
                    counts[vote] = 0
                counts[vote] += 1

            scounts = sorted(counts, key=lambda key: counts[key])
            res = ['%d. %s - %d votes' % (index, poll['options'][option], counts[option]) \
                for (index, option) in enumerate(scounts)]

            await cxt.say(self.codeblock('', '\n'.join(res)))

    async def c_vote(self, message, args, cxt):
        '''`j!vote poll_id option|"list"` - vote/list options in a poll'''

        try:
            poll_id = args[1]
            op = args[2]
        except:
            await cxt.say("Error parsing your shit :poop:")
            return

        if poll_id not in self.polls:
            await cxt.say("Poll not found")
            return

        author_id = str(message.author.id)
        poll = self.polls[poll_id]

        if op == 'list':
            # o n e l i n e s
            opts = ['%d. %s' % (idx, opt) for (idx, opt) \
                in enumerate(poll['options'])]

            await cxt.say("Poll: %s\nOptions: `%s`", \
                (poll['title'], '\n'.join(opts)))
        else:
            if poll['closed']:
                await cxt.say("This poll is closed.")
                return

            try:
                option = int(op) - 1
            except:
                await cxt.say("Your option is not a number")
                return

            if author_id in poll['votes']:
                await cxt.say("You already voted in this poll")
                return

            try:
                option_str = poll['options'][option]
            except IndexError:
                await cxt.say("Option not found")
                return

            poll['votes'][author_id] = option
            await cxt.say("<@%s> voted on option %d, %s", \
                (author_id, option, option_str))

            self.jsondb_save('polls')
