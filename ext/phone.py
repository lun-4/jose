from .common import Cog


class Phone(Cog):
    """Yes, you heard that right. Telephone.

    Not really a voice telephone. This is an idea into how it would work.
    """
    pass


def setup(bot):
    bot.add_cog(Phone(bot))
