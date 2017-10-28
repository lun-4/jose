import logging

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
        'succ',
        'No.',
    ],
)


class JoseChat(Cog):
    def __init__(self, bot):
        super().__init__(bot)
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
                'chatterbot.logic.TimeLogicAdapter',
                {
                    'import_path': 'chatterbot.logic.LowConfidenceAdapter',
                    'threshold': 0.6,
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
    @commands.cooldown(2, 5, commands.BucketType.default)
    async def chat(self, ctx, *, user_input: str):
        """Talk to the chatbot"""
        future = self.loop.run_in_executor(None,
                                           self.chatbot.get_response,
                                           user_input)
        response = await future
        await ctx.send(response)


def setup(bot):
    bot.add_cog(JoseChat(bot))
