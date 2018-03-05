import struct
import logging
import base64
import binascii
import contextlib
import io
import inspect
import time

import discord
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


def encode_inst(int_inst) -> bytes:
    return struct.pack('B', int_inst)


async def assembler(ctx, program: str):
    lines = program.split('\n')
    bytecode = []

    for line in lines:
        words = line.split(' ')
        command = words[0]

        if command == 'pushint':
            bytecode.append(encode_inst(Instructions.PUSH_INT))
            num = int(words[1])
            bytecode.append(struct.pack('i', num))
        elif command == 'pushstr':
            bytecode.append(encode_inst(Instructions.PUSH_STR))
            string = ' '.join(words[1:])
            bytecode.append(struct.pack('Q', len(string)))
            bytecode.append(string.encode('utf-8'))
        elif command == 'pop':
            bytecode.append(encode_inst(Instructions.SHOW_POP))
        elif command == 'add':
            bytecode.append(encode_inst(Instructions.ADD))
        else:
            raise ctx.cog.SayException(f'Invalid instruction: `{command}`')

    return b''.join(bytecode)


class JoseVM:
    """An instance of the José Virutal Machine."""
    def __init__(self, ctx, bytecode):
        #: Command context, in the case we want to echo
        self.ctx = ctx

        #: Program bytecode
        self.bytecode = bytecode

        #: Holds current instruction being executed
        self.running_op = -1

        #: Executed op count
        self.op_count = 0

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
        self.push(string)

    async def add_op(self):
        """Pop 2. Add them. Push the result."""
        res = self.pop() + self.pop()
        self.push(res)

    async def show_top(self):
        """Send a message containing the current top of the stack."""
        top = self.stack[len(self.stack) - 1]
        print(top)

    async def show_pop(self):
        """Send a message containing the result of a pop."""
        print(self.pop())

    async def view_stack(self):
        print(self.stack)

    async def run(self):
        """Run the VM in a loop."""
        while True:
            if self.pcounter >= len(self.bytecode):
                return

            instruction = await self.get_instruction()
            try:
                self.running_op = instruction
                func = self.map[instruction]
            except KeyError:
                raise VMError(f'Invalid instruction: {instruction!r}')

            await func()
            self.op_count += 1


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
        em = discord.Embed(title='José VM error',
                           color=discord.Color.red())

        em.add_field(name='program counter',
                     value=vm.pcounter,
                     inline=False)

        em.add_field(name='stack at moment of crash',
                     value=repr(vm.stack),
                     inline=True)

        # I'm already hating dir() enough.
        attributes = inspect.getmembers(Instructions,
                                        lambda a: not inspect.isroutine(a))

        names = [a for a in attributes if
                 not(a[0].startswith('__') and a[0].endswith('__'))]
        rev_names = {v: k for k, v in names}

        em.add_field(name='executing instruction',
                     value=rev_names.get(vm.running_op))

        em.add_field(name='error',
                     value=repr(err))

        await ctx.send(embed=em)

    async def assign_and_exec(self, ctx, bytecode: str):
        """Create a VM, assign to the user and run the VM."""
        if ctx.author in self.vms:
            raise self.SayException('You already have a VM running.')

        jvm = JoseVM(ctx, bytecode)
        self.vms[ctx.author.id] = jvm

        em = discord.Embed(title='José VM',
                           color=discord.Color.blurple())

        try:
            out = io.StringIO()
            t_start = time.monotonic()
            with contextlib.redirect_stdout(out):
                await jvm.run()
            t_end = time.monotonic()

            time_taken = round((t_end - t_start) * 1000, 4)

            em.add_field(name='executed instructions',
                         value=jvm.op_count, inline=False)
            em.add_field(name='time taken',
                         value=f'`{time_taken}ms`', inline=False)
            em.add_field(name='output',
                         value=out.getvalue() or '<no stdout>')
            await ctx.send(embed=em)
        except VMError as err:
            await self.print_traceback(ctx, jvm, err)
        except Exception as err:
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
    async def assemble(self, ctx, *, program: str):
        """Call the assembler on your code."""
        bytecode = await assembler(ctx, program)
        await ctx.send(base64.b64encode(bytecode).decode('utf-8'))

    @commands.command()
    async def run(self, ctx, *, program: str):
        """Assemble code and execute."""
        bytecode = await assembler(ctx, program)
        await self.assign_and_exec(ctx, bytecode)


def setup(bot):
    bot.add_cog(VM(bot))
