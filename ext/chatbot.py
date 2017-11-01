import logging
import discord

from chatterbot import ChatBot
from discord.ext import commands

from .common import Cog

log = logging.getLogger(__name__)

TRAINING = (
    [
        'Hi',
        'Hello!',
        'How are you?',
        "I'm fine, what about you?",
        "I'm good.",
        'Good to hear!'
    ],
    [
        'What are you up to?',
        'Talking to you.',
    ],
    [
        'hi',
        'go away',
        'ok',
        'bye loser',
    ],
    [
        'José',
        "What's good meme boy?",
        "I'm feeling fresh as fuck",
        "That's good to hear"
    ],
    [
        'lit',
        "What's lit lmao",
        'you',
        "Aww that's kind"
    ],
    [
        "Somebody once told me the world is gonna roll me",
        "I ain't the sharpest tool in the shed",
        "She was looking kind of dumb with her finger and her thumb",
        "In the shape of an \"L\" on her forehead",
        "Well the years start coming and they don't stop coming",
        "Fed to the rules and I hit the ground running",
        "Didn't make sense not to live for fun",
        "Your brain gets smart but your head gets dumb",
        "So much to do, so much to see",
        "So what's wrong with taking the back streets?",
        "You'll never know if you don't go",
        "You'll never shine if you don't glow",
        "Hey now, you're an all-star, get your game on, go play",
        "Hey now, you're a rock star, get the show on, get paid",
        "And all that glitters is gold",
        "Only shooting stars break the mold",
        "It's a cool place and they say it gets colder",
        "You're bundled up now, wait till you get older",
        "But the meteor men beg to differ",
        "Judging by the hole in the satellite picture",
        "The ice we skate is getting pretty thin",
        "The water's getting warm so you might as well swim",
        "My world's on fire, how about yours?",
        "That's the way I like it and I never get bored",
    ],
    [
        'Tell me a joke',
        "I'm not just here for your entertainment, I have feelings you know"
    ],
    [
        'Say something funny',
        "I'm not just here for your entertainment, I have feelings you know"
    ],
    [
        'Say something funny',

        "Idk how to make you laugh since you've "
        "already seen the funniest joke ever",

        'What?',
        'You HAHA REKT'
    ],
    [
        "I'm gay lol",
        "Tatsu is just a side hoe"
    ],
    [
        'Communism'

        'Death is a preferable alternative to communism. '
        'Capitalism all the way baby'
    ],
    [
        'Capitalism is great',
        'Communism is better!',
        'Wrong! Joseism is better'
    ],
    [
        'Who is your creator?',
        'Luna'
    ],
    [
        'Say something',
        'idk my dude'
    ],
    [
        'Good night',
        'Sweet dreams'
    ],
    [
        'Good morning',
        'Hello'
    ],
    [
        'You were already José',
        'Nani!?'
    ],
    [
        'Omae wa moe José',
        'Nani?!'
    ],
    [
        'What?',
        "I don't know my dude",
    ],
    [
        'We are one',
        'We are legion'
    ],
    [
        "You're a big guy",
        'For you',
    ],
)


class JoseChat(Cog):
    def __init__(self, bot):
        super().__init__(bot)
        self.whitelist = self.config.jose_db['chatbot_whitelist']

        self.chatbot = ChatBot(
            'José',
            trainer='chatterbot.trainers.ListTrainer',

            preprocessors=[
                'chatterbot.preprocessors.clean_whitespace',
                'chatterbot.preprocessors.unescape_html',
            ],

            logic_adapters=[
                'chatterbot.logic.BestMatch',
                'chatterbot.logic.MathematicalEvaluation',
                {
                    'import_path': 'chatterbot.logic.LowConfidenceAdapter',
                    'threshold': 0.2,
                    'default_response': 'I do not understand.'
                }
            ],

            input_adapter="chatterbot.input.VariableInputTypeAdapter",
            output_adapter="chatterbot.output.OutputAdapter"
        )

    @commands.command()
    @commands.is_owner()
    async def train(self, ctx):
        """Train the chatbot with the default conversations."""
        for convo in TRAINING:
            self.chatbot.train(convo)
        await ctx.send(f'Trained {len(TRAINING)} Conversations.')

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.default)
    async def chat(self, ctx, *, user_input: str):
        """Talk to the chatbot.

        This is completly separated from José's markov feature,
        the one you use through 'j!spt' and 'jose thing' messages.

        It is not "mixing words and sentences" together like
        markov did. This is Machine Learning and it will use
        previous inputs to it as-is.

        Powered by Chatterbot, kudos to them.
        """
        ok = await self.whitelist.find_one({'user_id': ctx.author.id})
        if not ok:
            raise self.SayException('You cannot use the chatbot.')

        with ctx.typing():
            future = self.loop.run_in_executor(None,
                                               self.chatbot.get_response,
                                               user_input)
            response = await future
            await ctx.send(response)

    @commands.group(aliases=['wl'])
    @commands.is_owner()
    async def whitelist(self, ctx):
        pass

    @whitelist.command(aliases=['add'])
    async def whitelist_add(self, ctx, person: discord.User):
        obj = {'user_id': person.id}
        r = await self.whitelist.insert_one(obj)
        await ctx.send(f'Inserted {r.inserted_count} documents')

    @whitelist.command(aliases=['remove'])
    async def whitelist_remove(self, ctx, person: discord.User):
        obj = {'user_id': person.id}
        r = await self.whitelist.delete_many(obj)
        await ctx.send(f'Deleted {r.deleted_count} documents')

    @chat.error
    async def error_handler(self, ctx, error):
        if isinstance(error, commands.errors.CommandOnCooldown):
            em = discord.Embed()

            em.description = 'You are being ratelimited, please retry in ' + \
                             f'`{error.retry_after:.2}` seconds'
            em.set_image(url='https://cdn.discordapp.com/attachments'
                         '/110373943822540800/183257679324643329'
                         '/b1nzybuddy.png')

            await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(JoseChat(bot))
