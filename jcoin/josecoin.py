import random
import time
import asyncio
import pickle

JOSECOIN_VERSION = '0.3'

JOSECOIN_HELP_TEXT = '''JoseCoin(%s) é a melhor moeda que o josé pode te oferecer!

Toda mensagem enviada tem 12%% de chance de conseguir 1, 1.2, 2, 2.5, 5, 5.1 ou 7.4JC$ para o autor da mensagem
Alguns comandos pedem JC$ em troca da sua funcionalidade(*comandos nsfw incluídos*)

!conta - cria uma nova conta
!enviar mention quantidade - envia josecoins para alguém
!saldo [mention] - mostra o quanto que tal conta tem em josecoins

''' % JOSECOIN_VERSION

data = {}
jose_id = '202587271679967232'

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

    print('acf', acc_from, 'act', acc_to, 'amount', amnt)
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
