import struct
import logging
import base64
import binascii

from discord.ext import commands

from .common import Cog

log = logging.getLogger(__name__)


class VMError(Exception):
    """General VM error."""
    pass


class VMEOFError(Exception):
    """Represents the end of a program's bytecode."""
    pass


class Instructions:
    """All the instructions in José VM Bytecode."""
    PUSH_INT = 1
    PUSH_UINT = 2
    PUSH_LONG = 3
    PUSH_ULONG = 4

    PUSH_STR = 5

    #: Send a message with the top of the stack.
    SHOW_TOP = 6
    SHOW_POP = 7

    ADD = 8
    VIEW = 9


async def josevm_compile(program: str):
    return b'\x01E\x00\x00\x00\x02'


class JoseVM:
    """An instance of the José Virutal Machine."""
    def __init__(self, ctx, bytecode):
        #: Command context, in the case we want to echo
        self.ctx = ctx

        #: Program bytecode
        self.bytecode = bytecode

        #: Program counter
        self.pcounter = 0

        #: Program stack and its length
        self.stack = []

        #: Loop counter, unused
        self.lcounter = 0

        #: Instruction handlers
        self.map = {
            Instructions.PUSH_INT: self.push_int,
            Instructions.PUSH_UINT: self.push_uint,

            Instructions.PUSH_LONG: self.push_long,
            Instructions.PUSH_ULONG: self.push_ulong,

            Instructions.PUSH_STR: self.push_str,

            Instructions.SHOW_TOP: self.show_top,
            Instructions.SHOW_POP: self.show_pop,

            Instructions.ADD: self.add_op,

            Instructions.VIEW: self.view_stack,
        }

    def push(self, val):
        """Push to the program's stack."""
        if len(self.stack) > 1000:
            raise VMError('Stack overflow')

        self.stack.append(val)

    def pop(self):
        """Pop from the program's stack."""
        value = self.stack.pop()
        return value

    async def read_bytes(self, bytecount):
        """Read an arbritary amount of bytes from the bytecode."""
        data = self.bytecode[self.pcounter:self.pcounter+bytecount]
        self.pcounter += bytecount
        return data

    async def read_int(self) -> int:
        """Read an integer."""
        data = await self.read_bytes(4)
        return struct.unpack('i', data)[0]

    async def read_uint(self) -> int:
        """Read an unsigned integer."""
        data = await self.read_bytes(4)
        return struct.unpack('I', data)[0]

    async def read_long(self):
        """Read a long long."""
        data = await self.read_bytes(8)
        return struct.unpack('q', data)[0]

    async def read_ulong(self):
        """Read an unsigned long long."""
        data = await self.read_bytes(8)
        return struct.unpack('Q', data)[0]

    def read_size(self):
        """read what is comparable to C's size_t."""
        return self.read_ulong()

    async def get_instruction(self) -> int:
        """Read one byte, comparable to a instruction"""
        data = await self.read_bytes(1)
        return struct.unpack('B', data)[0]

    # instruction handlers

    async def push_int(self):
        """Push an integer into the stack."""
        integer = await self.read_int()
        self.push(integer)

    async def push_uint(self):
        """Push an unsigned integer into the stack."""
        integer = await self.read_uint()
        self.push(integer)

    async def push_long(self):
        """Push a long into the stack."""
        longn = await self.read_long()
        self.push(longn)

    async def push_ulong(self):
        """Push an unsigned long into the stack."""
        longn = await self.read_ulong()
        self.push(longn)

    async def push_str(self):
        """Push a UTF-8 encoded string into the stack."""
        string_len = await self.read_size()
        string = await self.read_bytes(string_len)
        string = string.decode('utf-8')
        await self.ctx.send(f'pushing {string_len} bytes, `{string!r}`')
        self.push(string)

    async def add_op(self):
        """Pop 2. Add them. Push the result."""
        res = self.pop() + self.pop()
        self.push(res)

    async def show_top(self):
        """Send a message containing the current top of the stack."""
        top = self.stack[len(self.stack) - 1]
        await self.ctx.send(top)

    async def show_pop(self):
        """Send a message containing the result of a pop."""
        await self.ctx.send(self.pop())

    async def view_stack(self):
        await self.ctx.send(self.stack)

    async def run(self):
        """Run the VM in a loop."""
        while True:
            if self.pcounter >= len(self.bytecode):
                raise VMEOFError('Reached EOF of bytecode.')

            instruction = await self.get_instruction()
            try:
                func = self.map[instruction]
            except KeyError:
                raise VMError(f'Invalid instruction: {instruction!r}')
            await func()


class VM(Cog):
    """José's Virtual Machine.

    This is a stack-based VM. There is no documentation other
    than reading the VM's source.

    You are allowed to have 1 VM running your code at a time.
    """
    def __init__(self, bot):
        super().__init__(bot)

        self.vms = {}

    async def print_traceback(self, ctx, vm, err):
        """Print a traceback of the VM."""

        message = (f'```\n{"="*10} José VM Error {"="*10}\n'
                   f'\tprogram counter: {vm.pcounter}, '
                   f'total bytecode len: {len(vm.bytecode)}\n'
                   f'\tstack: {vm.stack!r}\n'
                   f'\terror: {err.args[0]}\n'
                   '\n```')

        raise self.SayException(message)

    async def assign_and_exec(self, ctx, bytecode: str):
        """Create a VM, assign to the user and run the VM."""
        if ctx.author in self.vms:
            raise self.SayException('You already have a VM running.')

        jvm = JoseVM(ctx, bytecode)
        self.vms[ctx.author.id] = jvm

        try:
            await jvm.run()
        except VMEOFError:
            await ctx.send('Program reached end of execution.')
        except VMError as err:
            await self.print_traceback(ctx, jvm, err)
        finally:
            self.vms.pop(ctx.author.id)

    @commands.command()
    async def run_compiled(self, ctx, data: str):
        """Receive a base64 representation of your bytecode and run it."""
        try:
            bytecode = base64.b64decode(data.encode('utf-8'))
        except binascii.Error:
            raise self.SayException('Invalid base64.')
        await self.assign_and_exec(ctx, bytecode)

    @commands.command()
    async def run(self, ctx, program: str):
        """runs a predefined program."""
        bytecode = await josevm_compile(program)
        await self.assign_and_exec(ctx, bytecode)


def setup(bot):
    bot.add_cog(VM(bot))
