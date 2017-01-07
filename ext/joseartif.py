#!/usr/bin/env python3

import discord
import asyncio
import sys

import txtutil

sys.path.append("..")
import jauxiliar as jaux
import joseerror as je

class JoseArtif(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)

    async def ext_load(self):
        return True, ''

    async def ext_unload(self):
        return True, ''

    async def e_on_message(self, message):
        # message as input
        msg = msg.content
        # process message (NLTK?)
        # analyze context
        # decision maker
        # response generator
        '''
        # generate 5 answers and the one with the best portuguese probability
        # (above 72%) gets said
        possible_answers = []
        answers = {}

        for answer in possible_answers:
            prob = txtutil.portuguese_probability(answer)
            if prob > .9:
                answers[answer] = prob

        answer_used = random.choice(answers)
        await self.say(answer_used)
        '''
        # output
        pass

    async def c_command(self, message, args):
        pass
