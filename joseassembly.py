
import asyncio
import discord

JASM_VERSION = '0.0.1'

JASM_HELP_TEXT = '''JoséAssembly é o melhor dialeto de Assembly que o José pode te oferecer!

A arquitetura do JASM

Comandos:

'''

def empty_env():
    return {
        'registers': {
            'r1': None,
            'r2': None,
            'r3': None,
            'r4': None,
            'r5': None,
            'r6': None,
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

@asyncio.coroutine
def execute(instructions, env):
    stdout = ''
    for inst in instructions:
        command = inst[0]
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
