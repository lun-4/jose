
import asyncio
import discord
import math

JASM_VERSION = '0.0.3'

JASM_HELP_TEXT = '''JoséAssembly é o melhor dialeto de Assembly que o José pode te oferecer!

A arquitetura do JASM tem 10 registradores que podem ser usados de qualquer forma.

Comandos e suas traduções:

mov a,b         a = b
add a,b         a = a + b
sub a,b         a = a - b
mul a,b         a = a * b
div a,b         a = a / b
pow a,b         a = a ** b
sqrt a          a = sqrt(a)

'''

def empty_env():
    return {
        'registers': {
            'r0': None,
            'r1': None,
            'r2': None,
            'r3': None,
            'r4': None,
            'r5': None,
            'r6': None,
            'r7': None,
            'r8': None,
            'r9': None,
        },
        'consts':{
            'JASM_VER': JASM_VERSION,
        },
    }

@asyncio.coroutine
def parse(text):
    insts = []
    for line in text.split('\n'):
        print(line)
        s = line.split(' ')
        command = s[0]
        args = ' '.join(s[1:])
        inst = [command, args]
        print(line, inst)
        insts.append(inst)
    return insts

def is_numeric(lit):
    'Return value of numeric literal string or ValueError exception'

    # Handle '0'
    if lit == '0': return 0
    # Hex/Binary
    litneg = lit[1:] if lit[0] == '-' else lit
    if litneg[0] == '0':
        if litneg[1] in 'xX':
            return int(lit,16)
        elif litneg[1] in 'bB':
            return int(lit,2)
        else:
            try:
                return int(lit,8)
            except ValueError:
                pass

    # Int/Float/Complex
    try:
        return int(lit)
    except ValueError:
        pass
    try:
        return float(lit)
    except ValueError:
        pass
    return complex(lit)

@asyncio.coroutine
def parse_value(val):
    if val[0] == '\"' and val[-1] == '\"':
        return val[1:-1]
    elif is_numeric(val):
        return is_numeric(val)
    else:
        return None

'''

mov r1,"nopOS. The OS that does nothing. Also known as Unoperational System. Made by TE VIRA"
write r1
nop
ret

'''

'''
    JASM Instruction set:

    MOV         A B     A = B

    ADD         A B     A = A + B
    SUB         A B     A = A - B
    MUL         A B     A = A * B
    DIV         A B     A = A / B
    POW         A B     A = A ^ B
    UNM         A B     A = -B

    BNOT        A B     A = not B
    BAND        A B     A = A and B
    BOR         A B     A = A or B

    WRITE       A       echo(a)

'''

def math_calc(opstr, inst, env):
    try:
        a, b = inst[1].split(',')
        if a not in env['registers']:
            return False, env, "first operand not found"

        if b not in env['registers']:
            return False, env, "second operand not found"

        val_a = env['registers'][a]
        val_b = env['registers'][b]

        if opstr == '+':
            env['registers'][a] = val_a + val_b
        elif opstr == '-':
            env['registers'][a] = val_a - val_b
        elif opstr == '*':
            env['registers'][a] = val_a * val_b
        elif opstr == '/':
            env['registers'][a] = val_a / val_b
        elif opstr == '^':
            env['registers'][a] = val_a ** val_b
        return True, env, ''
    except Exception as e:
        return False, env, 'pyerr: %s' % str(e)

@asyncio.coroutine
def execute(instructions, env):
    stdout = ''
    for inst in instructions:
        command = inst[0].lower()
        if command == 'mov' or command == 'set':
            try:
                reg, val = inst[1].split(',')
                # stdout += '%r %r' % (reg, val)
                val = yield from parse_value(val)

                if val is None:
                    return False, env, 'erro parseando valor'

                if reg in env['registers']:
                    env['registers'][reg] = val
                    # stdout += "set %r to %r" % (reg, val)
                else:
                    return False, env, 'registrador não encontrado'
            except Exception as e:
                return False, env, 'pyerr: %s' % str(e)

        # maths
        elif command == 'add':
            res = math_calc('+', inst, env)
            env = res[1]
            if not res[0]:
                return False, env, res[2]
        elif command == 'sub':
            res = math_calc('-', inst, env)
            env = res[1]
            if not res[0]:
                return False, env, res[2]

        elif command == 'mul':
            res = math_calc('*', inst, env)
            env = res[1]
            if not res[0]:
                return False, env, res[2]
        elif command == 'div':
            res = math_calc('/', inst, env)
            env = res[1]
            if not res[0]:
                return False, env, res[2]
        elif command == 'pow':
            res = math_calc('^', inst, env)
            env = res[1]
            if not res[0]:
                return False, env, res[2]

        elif command == 'sqrt':
            try:
                reg = inst[1]

                env['registers'][reg] = math.sqrt(env['registers'][reg])
            except Exception as e:
                return False, env, 'pyerr: %s' % str(e)

        elif command == 'nop':
            pass

        elif command == 'ret':
            return True, env, ''

        elif command == 'write':
            try:
                reg = inst[1]
                if reg in env['registers']:
                    stdout += '%s\n' % env['registers'][reg]
                else:
                    return False, env, 'registrador não encontrado'
            except:
                return False, env, 'pyerr: %s' % str(e)

        else:
            return False, env, "nenhum comando encontrado"
    return True, env, stdout
