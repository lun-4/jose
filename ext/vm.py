import contextlib
import logging
import io

from discord.ext import commands

from .common import Cog

log = logging.getLogger(__name__)


class Instructions:
    """All the instructions in José VM Bytecode."""
    PUSH_INT = 1
    PUSH_STR = 2
    POP = 3
    CALL_ADD = 4


class JoseVM:
    def __init__(self, program):
        self.program = program
        self.pc = 0
        self.stack = []
        self.handlers = {}

    def read_byte(self):
        self.pc += 1
        return self.program[self.pc]

    def read_bytes(self, bytecount: int):
        data = self.program[self.pc:self.pc + bytecount]
        self.pc += bytecount
        return data

    def pull_int(self):
        return int(self.pull_bytes(4))

    def i_push(self):
        a = self.pull_value()
        self.stack.append(a)

    def i_pop(self):
        self.stack.pop()

    def i_add(self):
        self.stack.append(self.stack.pop() + self.stack.pop())

    def i_pprint(self):
        print(self.stack.pop())

    def execute(self):
        """Execute."""
        while True:
            try:
                inst = self.read_byte()
                self.handler[self.read_byte()]
            except KeyError:
                break


class VM(Cog):
    """José's virtual machine

    This can execute José VM Bytecode.
    """
    def __init__(self, bot):
        super().__init__(bot)

    @commands.command()
    async def compile(self, code: str):
        """Compile code to JoséVM Instructions"""
        pass

    @commands.command()
    async def execute(self, ctx, data: str):
        vm = JoseVM(data)
        out = io.StringIO()

        with contextlib.redirect_stdout(out):
            vm.execute()

        data = out.read()
        if len(data) > 2000:
            raise self.SayException('big output = big nono')

        await ctx.send(data)


def setup(bot):
    bot.add_cog(VM(bot))
