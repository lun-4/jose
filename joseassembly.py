
import asyncio
import discord
import cmath as math
import time

JASM_VERSION = '0.2'

JASM_HELP_TEXT = '''JoséAssembly(v%s) é o melhor dialeto de Assembly que o José pode te oferecer!

A arquitetura do JASM tem 10 registradores que podem ser usados de qualquer forma.

Comandos e suas traduções:

mov a,b         a = b
add a,b         a = a + b
sub a,b         a = a - b
mul a,b         a = a * b
div a,b         a = a / b
pow a,b         a = a ** b
sqrt a          a = sqrt(a)

''' % JASM_VERSION

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
            'r10': None,
            'r11': None,
            'r12': None,
            'r13': None,
            'r14': None,
            'r15': None,
            'r16': None,
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
def parse_value(val, env):
    if val[0] == '$':
        reg = val[val.find('(')+1:val.find(')')]
        return env['registers'][reg]
    elif val[0] == '\"' and val[-1] == '\"':
        return val[1:-1]
    else:
        try:
            return is_numeric(val)
        except:
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

'''
test comparison:

mov r1,1
mov r2,1
cmp r1,r2
mov r10,"equal"
else
mov r10,"not equal"
cmpe
write r10
'''

'''
loops:


mov r1,0
mov r2,15
.loop r5

inc r1
echo r1
blet r1,r2,r5 # boolean less than or equal
bnot r5 # boolean not

lpe # loop end

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
        elif opstr == 'u':
            env['registers'][a] = -val_b
        return True, env, ''
    except Exception as e:
        return False, env, 'pyerr: %s' % str(e)

@asyncio.coroutine
def execute(instructions, env):
    stdout = ''
    pc = 0 # program counter
    print("execute %r" % instructions)
    # time.sleep(2)
    while pc < len(instructions):
        inst = instructions[pc]
        print("instruction: %r" % inst)
        if inst == ['', '']:
            pc += 1
            continue

        if len(inst[0]) > 1:
            if inst[0][0] == '#':
                pc += 1
                continue
        else:
            pass
        command = inst[0].lower()

        if command.strip() == '':
            pc += 1
            continue
        elif command == '#' or command == '':
            pc += 1
            continue
        elif command == 'mov' or command == 'set':
            try:
                reg, val = inst[1].split(',')
                # stdout += '%r %r' % (reg, val)
                val = yield from parse_value(val, env)

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
        elif command == 'unm':
            res = math_calc('u', inst, env)
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
                    stdout += '%s' % env['registers'][reg]
                else:
                    return False, env, 'registrador não encontrado'
            except Exception as e:
                return False, env, 'pyerr: %s' % str(e)

        elif command == 'echo':
            try:
                reg = inst[1]
                if reg in env['registers']:
                    stdout += '%s\n' % env['registers'][reg]
                else:
                    return False, env, 'registrador não encontrado'
            except Exception as e:
                return False, env, 'pyerr: %s' % str(e)

        elif command == 'cmp':
            try:
                rega, regb = inst[1].split(',')

                if rega not in env['registers']:
                    return False, env, 'registrador não encontrado'

                if regb not in env['registers']:
                    return False, env, 'registrador não encontrado'

                val_a = env['registers'][rega]
                val_b = env['registers'][regb]

                print('cmp', val_a, val_b, val_a == val_b)

                if val_a == val_b:
                    pc += 1
                    # start from here
                    continue
                else:
                    # increment PC until 'else'(or cmpe found) found
                    while True:
                        if inst[0].lower() == 'else': break
                        if inst[0].lower() == 'cmpe': break
                        pc += 1
                        inst = instructions[pc]
                    pc += 1 # step else
                    continue #work it on from it

            except Exception as e:
                return False, env, 'pyerr: %s' % str(e)

        elif command == 'else':
            # increment until cmpe
            while True:
                if inst[0].lower() == 'cmpe': break
                pc += 1
                inst = instructions[pc]
            pc += 1 #step cmpe
            continue

        elif command == 'cmpe':
            pass

        else:
            return False, env, "comando %r não encontrado" % command

        pc += 1
    return True, env, stdout
