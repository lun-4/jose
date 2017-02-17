import time
import asyncio
import pickle

import sys
sys.path.append("..")
import josecommon as jcommon
import joseerror as je

JOSECOIN_VERSION = '0.6'

import decimal
decimal.getcontext().prec = 3

JOSECOIN_HELP_TEXT = '''JoseCoin(%s) é a melhor moeda que o josé pode te oferecer!

Toda mensagem enviada tem 1%% de chance de conseguir 1, 1.2, 2, 2.5, 5, 5.1 ou 7.4JC$ para o autor da mensagem
Alguns comandos pedem JC$ em troca da sua funcionalidade(*comandos nsfw incluídos*)

!conta - cria uma nova conta
!enviar mention quantidade - envia josecoins para alguém
!saldo [mention] - mostra o quanto que tal conta tem em josecoins

''' % JOSECOIN_VERSION

data = {}
jose_id = jcommon.JOSE_ID

LEDGER_PATH = 'jcoin/josecoin-5.journal'

def ledger_data(fpath, data):
    with open(fpath, 'a') as f:
        f.write(data)
    return

def empty_acc(name, amnt):
    return {
        'amount': amnt,
        'name': name
    }

def new_acc(id_acc, name, init_amnt=None):
    if init_amnt is None:
        # the readjust gave so little prices I need to lower this
        init_amnt = decimal.Decimal('3')

    if id_acc in data:
        return False, 'account already exists'

    data[id_acc] = empty_acc(name, init_amnt)
    return True, 'account made with success'

def get(id_acc):
    if id_acc not in data:
        return False, 'account doesn\'t exist'
    return True, data[id_acc]

def gen():
    for acc_id in data:
        acc = data[acc_id]
        yield (acc_id, acc['name'], acc['amount'])

def transfer(id_from, id_to, amnt, file_name):
    amnt = decimal.Decimal(str(amnt))

    if amnt < 0:
        return False, "values less than zero aren't permitted"

    if amnt == 0:
        return False, "sending zero is prohibited"

    if not (id_from in data):
        return False, "account to get funds doesn't exist"

    if not (id_to in data):
        return False, "account to send funds doesn't exist"

    try:
        acc_from = data[id_from]
        acc_to = data[id_to]
    except Exception as e:
        return False, str(e)

    print('from', acc_from, 'to', acc_to, 'amount', amnt)
    if not (acc_from['amount'] >= amnt):
        return False, "account doesn't have enough funds to make this transaction"

    acc_to['amount'] += amnt
    acc_from['amount'] -= amnt

    ledger_data(file_name, "%f;TR;%s;%s;%s\n" % (time.time(), id_from, id_to, amnt))

    return True, "%s was sent from %s to %s" % (amnt, acc_from['name'], acc_to['name'])

def load(fname):
    global data
    try:
        with open(fname, 'rb') as f:
            data = pickle.load(f)
    except Exception as e:
        return False, str(e)

    data[jose_id] = empty_acc('jose-bot', decimal.Decimal('1000000'))
    #ledger_data(fname.replace('db', 'journal'), '%f;LOAD;%r\n' % (time.time(), data))
    return True, "load %s" % fname

def save(fname):
    global data
    try:
        with open(fname, 'wb') as f:
            pickle.dump(data, f)
    except Exception as e:
        return False, str(e)

    #ledger_data(fname.replace('db', 'journal'), '%f;SAVE;%r\n' % (time.time(), data))
    return True, "save %s" % fname

async def jcoin_control(userid, amount):
    return transfer(userid, jose_id, amount, LEDGER_PATH)

async def raw_save():
    res = save('jcoin/josecoin.db')
    return res

class JoseCoin(jcommon.Extension):
    def __init__(self, cl):
        global data
        jcommon.Extension.__init__(self, cl)
        self.top10_flag = False
        self.data = data

    async def josecoin_save(self, message, dbg_flag=True):
        self.current = message
        res = save('jcoin/josecoin.db')
        if not res[0]:
            await self.client.send_message(message.channel, "err: `%r`" % res)

    async def josecoin_load(self, message, dbg_flag=True):
        self.current = message
        res = load('jcoin/josecoin.db')
        if not res[0]:
            await self.client.send_message(message.channel, "err: `%r`" % res)

    async def c_saldo(self, message, args, cxt):
        '''`!saldo [@mention]` - mostra o saldo seu ou de outra pessoa'''
        args = message.content.split(' ')

        id_check = None
        if len(args) < 2:
            id_check = message.author.id
        else:
            id_check = await jcommon.parse_id(args[1], message)

        res = get(id_check)
        if res[0]:
            accdata = res[1]
            await cxt.say(('%s -> %.2f' % (accdata['name'], accdata['amount'])))
        else:
            await cxt.say('account not found(`id:%s`)' % (id_check))

    async def c_conta(self, message, args, cxt):
        print("new jcoin account %s" % message.author.id)

        res = new_acc(message.author.id, str(message.author))
        if res[0]:
            await cxt.say(res[1])
        else:
            await cxt.say('jc->err: %s' % res[1])

    async def c_write(self, message, args, cxt):
        '''`!write @mention new_amount` - sobrescreve o saldo de uma conta'''
        global data
        await self.is_admin(message.author.id)

        id_from = await jcommon.parse_id(args[1], message)
        new_amount = decimal.Decimal(args[2])

        data[id_from]['amount'] = new_amount
        await cxt.say("<@%s> has %.2fJC now" % (id_from, data[id_from]['amount']))

    async def c_enviar(self, message, args, cxt):
        '''`!enviar @mention quantidade` - envia JCoins para uma conta'''

        if len(args) != 3:
            await cxt.say(self.c_enviar.__doc__)
            return

        id_to = args[1]
        try:
            amount = decimal.Decimal(args[2])
        except ValueError:
            await cxt.say("ValueError: error parsing value")
            return
        except Exception as e:
            await cxt.say("Exception: `%r`" % e)
            return

        id_from = message.author.id
        id_to = await jcommon.parse_id(id_to, message)

        res = transfer(id_from, id_to, amount, LEDGER_PATH)
        await self.josecoin_save(message, False)
        if res[0]:
            await cxt.say(res[1])
        else:
            await cxt.say('jc_err: `%s`' % res[1])

    async def c_top10(self, message, args, cxt):
        jcdata = dict(data) # copy

        range_max = 11 # default 10 users
        if len(args) > 1:
            range_max = int(args[1]) + 1

        maior = {
            'id': 0,
            'name': '',
            'amount': 0.0,
        }

        if range_max >= 16:
            await cxt.say("LimitError: values higher than 16 aren't valid")
            return
        elif range_max <= 0:
            await cxt.say("haha no")
            return

        order = []

        for i in range(1,range_max):
            if len(jcdata) < 1:
                break

            for accid in jcdata:
                acc = jcdata[accid]
                name, amount = acc['name'], acc['amount']
                if amount > maior['amount']:
                    maior['id'] = accid
                    maior['name'] = name
                    maior['amount'] = amount

            del jcdata[maior['id']]
            order.append('%d. %s -> %.2f' % (i, maior['name'], maior['amount']))

            # reset to next
            maior = {
                'id': 0,
                'name': '',
                'amount': 0.0,
            }

        await cxt.say('\n'.join(order))
        return
