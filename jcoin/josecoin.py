import random
import time
import asyncio
import pickle

import sys
sys.path.append("..")
import josecommon as jcommon
import joseerror as je

JOSECOIN_VERSION = '0.4.2'

JOSECOIN_HELP_TEXT = '''JoseCoin(%s) é a melhor moeda que o josé pode te oferecer!

Toda mensagem enviada tem 12%% de chance de conseguir 1, 1.2, 2, 2.5, 5, 5.1 ou 7.4JC$ para o autor da mensagem
Alguns comandos pedem JC$ em troca da sua funcionalidade(*comandos nsfw incluídos*)

!conta - cria uma nova conta
!enviar mention quantidade - envia josecoins para alguém
!saldo [mention] - mostra o quanto que tal conta tem em josecoins

''' % JOSECOIN_VERSION

data = {}
jose_id = jcommon.JOSE_ID

LEDGER_PATH = 'jcoin/josecoin-2.journal'

def ledger_data(fpath, data):
    with open(fpath, 'a') as f:
        f.write(data)
    return

def empty_acc(name, amnt):
    return {
        'amount': amnt,
        'name': name
    }

def new_acc(id_acc, name, init_amnt=25.0):
    if id_acc in data:
        return False, 'conta já existe'

    data[id_acc] = empty_acc(name, init_amnt)
    return True, 'conta criada com sucesso'

def get(id_acc):
    if id_acc not in data:
        return False, 'conta não existe'
    return True, data[id_acc]

def gen():
    for acc_id in data:
        acc = data[acc_id]
        yield (acc_id, acc['name'], acc['amount'])

def transfer(id_from, id_to, amnt, file_name):
    amnt = float(amnt)

    if amnt < 0:
        return False, "valores menores do que zero não são permitidos"

    if not (id_from in data):
        return False, 'conta para extrair fundos não existe'

    if not (id_to in data):
        return False, 'conta de destino não existe'

    try:
        acc_from = data[id_from]
        acc_to = data[id_to]
    except Exception as e:
        return False, str(e)

    print('from', acc_from, 'to', acc_to, 'amount', amnt)
    if not (acc_from['amount'] >= amnt):
        return False, "conta não possui fundos suficientes para a transação"

    acc_to['amount'] += amnt
    acc_from['amount'] -= amnt

    ledger_data(file_name, "%f;TR;%s;%s;%f\n" % (time.time(), id_from, id_to, amnt))

    return True, "%.2f foram enviados de %s para %s" % (amnt, acc_from['name'], acc_to['name'])

def load(fname):
    global data
    try:
        with open(fname, 'rb') as f:
            data = pickle.load(f)
    except Exception as e:
        return False, str(e)

    # data[jose_id] = empty_acc('jose-bot', 50000)
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

@asyncio.coroutine
def jcoin_control(userid, amount):
    return transfer(userid, jose_id, amount, LEDGER_PATH)

class JoseCoin(jcommon.Extension):
    def __init__(self, cl):
        self.client = cl
        self.current = None
        self.top10_flag = False
        jcommon.Extension.__init__(self, cl)

    async def josecoin_save(self, message, dbg_flag=True):
        self.current = message
        await self.debug("saving josecoin data", dbg_flag)
        res = save('jcoin/josecoin.db')
        if not res[0]:
            await self.debug('error: %r' % res)

    async def josecoin_load(self, message, dbg_flag=True):
        self.current = message
        await self.debug("loading josecoin data", dbg_flag)
        res = load('jcoin/josecoin.db')
        if not res[0]:
            await self.debug('error: %r' % res)

    async def c_saldo(self, message, args):
        args = message.content.split(' ')

        id_check = None
        if len(args) < 2:
            id_check = message.author.id
        else:
            id_check = await jcommon.parse_id(args[1], message)

        res = get(id_check)
        if res[0]:
            accdata = res[1]
            await self.say('%s -> %.2f' % (accdata['name'], accdata['amount']))
        else:
            await self.say('erro encontrando conta(id: %s)' % (id_check))

    async def c_conta(self, message, args):
        print("new jcoin account %s" % message.author.id)

        res = new_acc(message.author.id, str(message.author))
        if res[0]:
            await self.say(res[1])
        else:
            await self.say('jc_error: %s' % res[1])

    async def c_write(self, message, args):
        global data
        auth = await self.rolecheck(jcommon.MASTER_ROLE)
        if not auth:
            await self.debug("PermissionError: sem permissão para alterar dados da JC")

        id_from = await jcommon.parse_id(args[1], message)
        new_amount = float(args[2])

        data[id_from]['amount'] = new_amount
        await self.say("conta <@%s>: %.2f" % (id_from, data[id_from]['amount']))

    async def c_top10(self, message, args):
        if self.top10_flag:
            raise je.LimitError()
        self.top10_flag = True
        jcdata = dict(data) # copy

        range_max = 11 # default 10 users
        if len(args) > 1:
            range_max = int(args[1]) + 1

        res = 'Top %d pessoas que tem mais JC$\n' % (range_max - 1)
        maior = {
            'id': 0,
            'name': '',
            'amount': 0.0,
        }

        if range_max >= 16:
            await self.say("LimitError: valores maiores do que 16 não válidos")
            #raise jcommon.LimitError()
            return

        print("top10 query")

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

        await self.say('\n'.join(order))
        self.top10_flag = False
