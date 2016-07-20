
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
        s = line.split(' ')
        command = s[0]
        args = ' '.join(s[1:])
        insts.append([command, args])
    return insts

@asyncio.coroutine
def execute(instructions, env):
    stdout = '> '
    for inst in instructions:
        if inst[0] == 'mov' or inst[0] == 'set':
            try:
                reg, val = inst[1].split(',')
                print('mov %r %r' % (reg, val))
                stdout += '%r %r' % (reg, val)
            except Exception as e:
                return False, env, str(e)
    return True, env, stdout
