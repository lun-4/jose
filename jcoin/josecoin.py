import random
import time
import asyncio
import pickle

#aaaaa
'''
<@196461455569059840>
<@!162819866682851329>
'''

JOSECOIN_VERSION = '0.2'

JOSECOIN_HELP_TEXT = '''JoseCoin(%s) é a melhor moeda que o josé pode te oferecer!

Toda mensagem enviada tem 12%% de chance de conseguir 2, 5, 10, 15 ou 20 JC$ para o autor da mensagem
Alguns comandos pedem JC$ em troca da sua funcionalidade(*comandos nsfw incluídos*)

!conta - cria uma nova conta
!enviar mention quantidade - envia josecoins para alguém
!saldo mention - mostra o quanto que tal conta tem em josecoins

''' % JOSECOIN_VERSION

data = {}
jose_id = '202587271679967232'

def empty_acc(name, amnt):
    return {
        'amount': amnt,
        'name': name
    }

def new_acc(id_acc, name, init_amnt=10.0):
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

def transfer(id_from, id_to, amnt):
    amnt = float(amnt)
    print('idf', id_from, 'idt', id_to)

    if not (id_from in data):
        return False, 'conta para extrair fundos não existe'

    if not (id_to in data):
        return False, 'conta de destino não existe'

    try:
        acc_from = data[id_from]
        acc_to = data[id_to]
    except Exception as e:
        return False, str(e)

    print('acf', acc_from, 'act', acc_to)
    print('amount', amnt)
    if not (acc_from['amount'] >= amnt):
        return False, "conta não possui fundos suficientes para a transação"

    acc_to['amount'] += amnt
    acc_from['amount'] -= amnt

    return True, "%.2f foram enviados de %s para %s" % (amnt, acc_from['name'], acc_to['name'])

def load(fname):
    global data
    with open(fname, 'rb') as f:
        data = pickle.load(f)

    # data[jose_id] = empty_acc('jose-bot', 2000)
    return True, "load %s" % fname

def save(fname):
    global data
    with open(fname, 'wb') as f:
        pickle.dump(data, f)
    return True, "save %s" % fname
